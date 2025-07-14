from flask import Flask, render_template, request, jsonify, make_response
import uuid

from firebase_config import initialise_firebase, get_firestore_client
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from datetime import datetime

app = Flask(__name__)

# Initialize Firebase on app startup
initialise_firebase()
db = get_firestore_client()

# --- Firestore structure ---
# Users are stored at users/[privateUserID]
USERS_COLLECTION = db.collection('users')
# The user list is stored at users/userList (as a document with a userList array - a list of public IDs)
USERLIST_DOC = db.collection('users').document('userList')

# Ensure userList doc exists on startup
if not USERLIST_DOC.get().exists:
    USERLIST_DOC.set({'userList': []})

# --- Routes ---

@app.route('/')
def index():
    """Return the main HTML template."""
    return render_template('index.html')

@app.route('/api/create_user', methods=['POST'])
def create_user():
    """Create a new user and add to Firestore and userList atomically."""
    data = request.get_json()
    nickname = data.get('nickname', '').strip()
    origin = data.get('origin', '').strip()
    if not nickname or not origin:
        return jsonify({'error': 'Nickname and origin are required.'}), 400
    if len(nickname) > 32:
        return jsonify({'error': f'Nickname must be at most 32 characters.'}), 400
    if len(origin) > 64:
        return jsonify({'error': f'Origin must be at most 64 characters.'}), 400

    private_user_id = str(uuid.uuid4())
    public_user_id = str(uuid.uuid4())

    user_obj = {
        'nickname': nickname,
        'origin': origin,
        'privateUserID': private_user_id,
        'publicUserID': public_user_id,
        'following': [],
        'followerCount': 0,
        'createdAt': datetime.utcnow().isoformat() + 'Z'
    }

    transaction = db.transaction()

    #Add user doc and update userList atomically
    @firestore.transactional
    def create_user_transaction(transaction, private_user_id, public_user_id, user_obj):

        # Get and update userList
        user_list_doc = USERLIST_DOC.get(transaction=transaction) # Reads must happen before writes
        user_list = user_list_doc.to_dict().get('userList', []) if user_list_doc.exists else [] 
        user_list.append(public_user_id)
        transaction.set(USERLIST_DOC, {'userList': user_list})

        # Add user doc
        user_doc_ref = USERS_COLLECTION.document(private_user_id)
        transaction.set(user_doc_ref, user_obj)

    create_user_transaction(transaction, private_user_id, public_user_id, user_obj)

    # Set privateUserID cookie for client
    resp = make_response(jsonify({'success': True, 'privateUserID': private_user_id}))
    resp.set_cookie('privateUserID', private_user_id, max_age=60*60*24*365)  # 1 year expiration
    return resp

@app.route('/api/user_info')
def get_user_info():
    """Return info for the current user (from cookie)."""
    private_user_id = request.cookies.get('privateUserID')
    if not private_user_id:
        return jsonify({'error': 'User not found'}), 404

    # Retrieve user document from Firestore and return to client if found
    user_doc = USERS_COLLECTION.document(private_user_id).get()
    if not user_doc.exists:
        return jsonify({'error': 'User not found'}), 404
    user = user_doc.to_dict()
    return jsonify({
        'nickname': user['nickname'],
        'origin': user['origin'],
        'privateUserID': user['privateUserID'],
        'publicUserID': user['publicUserID'],
        'following': user['following'],
        'followerCount': user['followerCount'],
        'createdAt': user.get('createdAt')
    })

@app.route('/api/users_feed')
def get_users_feed():
    """Return a paginated feed of users (excluding the current user)."""
    private_user_id = request.cookies.get('privateUserID')
    if not private_user_id:
        return jsonify({'error': 'No user ID provided in request'}), 404

    # Retrieve user doc and extract public_user_id
    user_doc = USERS_COLLECTION.document(private_user_id).get()
    if not user_doc.exists:
        return jsonify({'error': 'User not found'}), 404
    feed_public_user_id = user_doc.to_dict().get('publicUserID')

    # Pagination parameters
    page = int(request.args.get('page', 1))
    per_page = 10
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Get userList from Firestore (a list of the public user IDs)
    user_list_doc = USERLIST_DOC.get()
    user_list = user_list_doc.to_dict().get('userList', []) if user_list_doc.exists else []

    # Exclude current user and get the requested page
    filtered_user_ids = [uid for uid in user_list if uid != feed_public_user_id]
    paged_user_ids = filtered_user_ids[start_idx:end_idx]  # Python slicing is safe
    has_more = end_idx < len(filtered_user_ids)

    # Build the feed with user info
    feed_users = []
    for uid in paged_user_ids:
        u_query = USERS_COLLECTION.where(filter=FieldFilter('publicUserID', '==', uid)).limit(1).get()
        u_doc = u_query[0] if u_query else None
        if u_doc.exists:
            u = u_doc.to_dict()
            feed_users.append({
                'nickname': u['nickname'],
                #'privateUserID': u['privateUserID'], THIS SHOULD NOT BE SENT BACK TO THE CLIENT AS IT EXPOSES ALL PRIVATE USER IDS!
                'publicUserID': u['publicUserID'],
                'origin': u['origin'],
                'isFollowing': uid in user_doc.to_dict().get('following', []),
                'followerCount':  u['followerCount'],
                'createdAt': u.get('createdAt')
            })

    return jsonify({
        'users': feed_users,
        'hasMore': has_more,
        'page': page
    })

@app.route('/api/follow_user', methods=['POST'])
def follow_user():
    """Add a user to the current user's following list (using their publicID) and update the follower count atomically."""
    private_user_id = request.cookies.get('privateUserID')
    if not private_user_id:
        return jsonify({'error': 'Following user id not found in request'}), 404

    data = request.get_json()
    target_public_user_id = data.get('targetPublicUserID')
    if not target_public_user_id:
        return jsonify({'error': 'Target user not found in request'}), 404

    transaction = db.transaction()

    # Transactionally check the users exist and update the following list
    @firestore.transactional
    def follow_user_transaction(transaction, private_user_id, target_public_user_id):

        # Check both users exist
        user_doc_ref = USERS_COLLECTION.document(private_user_id)
        user_doc = user_doc_ref.get(transaction=transaction)
        if not user_doc.exists:
            return {'error': 'Following user not found'}, 404

        target_user_query = USERS_COLLECTION.where(filter=FieldFilter('publicUserID', '==', target_public_user_id)).limit(1).get(transaction=transaction)
        target_user_doc = target_user_query[0] if target_user_query else None
        target_private_user_id = target_user_doc.to_dict()['privateUserID'] # Needed to read and write back to target users data
        target_user_doc_ref = USERS_COLLECTION.document(target_private_user_id)
        if not target_user_doc.exists:
            return {'error': 'Target user not found'}, 404

        # Update following list
        user_data = user_doc.to_dict()
        if target_public_user_id in user_data['following']:
            return {'error': 'Already following user'}, 400
        user_data['following'].append(target_public_user_id)
        transaction.update(user_doc_ref, {'following': user_data['following']})

        # Update follower count
        target_user_data = target_user_doc.to_dict()
        transaction.update(target_user_doc_ref, {'followerCount': target_user_data['followerCount'] + 1})

        return {'success': True}, 200

    result, status = follow_user_transaction(transaction, private_user_id, target_public_user_id)
    return jsonify(result), status

if __name__ == '__main__':
    app.run(debug=True)

#TODO: 
    # User pps - can these be random Avatars? 

