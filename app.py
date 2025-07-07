from flask import Flask, render_template, request, jsonify, make_response
import uuid
from firebase_config import initialise_firebase, get_firestore_client

app = Flask(__name__)

# Initialize Firebase on app startup
initialise_firebase()
db = get_firestore_client()

# --- Firestore structure ---
# Users are stored at users/[userID]
USERS_COLLECTION = db.collection('users')
# The user list is stored at users/userList (as a document with a userList array)
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
    """Create a new user and add to Firestore and userList."""
    data = request.get_json()
    nickname = data.get('nickname', '').strip()
    origin = data.get('origin', '').strip()
    if not nickname or not origin:
        return jsonify({'error': 'Nickname and origin are required.'}), 400

    user_id = str(uuid.uuid4())
    user_obj = {
        'nickname': nickname,
        'origin': origin,
        'userID': user_id,
        'following': []
    }

    # Store user in Firestore
    USERS_COLLECTION.document(user_id).set(user_obj)

    # Add userID to userList in Firestore
    user_list_doc = USERLIST_DOC.get()
    user_list = user_list_doc.to_dict().get('userList', []) if user_list_doc.exists else []
    user_list.append(user_id)
    USERLIST_DOC.set({'userList': user_list})

    # Set userID cookie for client
    resp = make_response(jsonify({'success': True, 'userID': user_id}))
    resp.set_cookie('userID', user_id, max_age=60*60*24*365)  # 1 year expiration
    return resp

@app.route('/api/user_info')
def get_user_info():
    """Return info for the current user (from cookie)."""
    user_id = request.cookies.get('userID')
    if not user_id:
        return jsonify({'error': 'User not found'}), 404

    # Retrieve user document from Firestore and return to client if found
    user_doc = USERS_COLLECTION.document(user_id).get()
    if not user_doc.exists:
        return jsonify({'error': 'User not found'}), 404
    user = user_doc.to_dict()
    return jsonify({
        'nickname': user['nickname'],
        'userID': user['userID'],
        'following': user['following']
    })

@app.route('/api/users_feed')
def get_users_feed():
    """Return a paginated feed of users (excluding the current user)."""
    user_id = request.cookies.get('userID')
    if not user_id:
        return jsonify({'error': 'No user ID provided'}), 404

    # Retrieve user doc
    user_doc = USERS_COLLECTION.document(user_id).get()
    if not user_doc.exists:
        return jsonify({'error': 'User not found'}), 404

    # Pagination parameters
    page = int(request.args.get('page', 1))
    per_page = 10
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Get userList from Firestore
    user_list_doc = USERLIST_DOC.get()
    user_list = user_list_doc.to_dict().get('userList', []) if user_list_doc.exists else []

    # Exclude current user and get the requested page
    filtered_user_ids = [uid for uid in user_list if uid != user_id]
    paged_user_ids = filtered_user_ids[start_idx:end_idx]  # Python slicing is safe
    has_more = end_idx < len(filtered_user_ids)

    # Build the feed with user info
    feed_users = []
    for uid in paged_user_ids:
        u_doc = USERS_COLLECTION.document(uid).get()
        if u_doc.exists:
            u = u_doc.to_dict()
            feed_users.append({
                'nickname': u['nickname'],
                'userID': u['userID'],
                'origin': u.get('origin', ''),
                'isFollowing': uid in user_doc.to_dict().get('following', [])
            })

    return jsonify({
        'users': feed_users,
        'hasMore': has_more,
        'page': page
    })

@app.route('/api/follow_user', methods=['POST'])
def follow_user():
    """Add a user to the current user's following list."""
    # Get userID from cookie and return if error
    user_id = request.cookies.get('userID')
    if not user_id:
        return jsonify({'error': 'User not found'}), 404

    # Retrieve user document for following user
    user_doc_ref = USERS_COLLECTION.document(user_id)
    user_doc = user_doc_ref.get()
    if not user_doc.exists:
        return jsonify({'error': 'User not found'}), 404

    # Check followed user exists
    data = request.get_json()
    target_user_id = data.get('targetUserID')
    target_user_doc = USERS_COLLECTION.document(target_user_id).get()
    if not target_user_id or not target_user_doc.exists:
        return jsonify({'error': 'Target user not found'}), 404

    # Can't follow yourself!
    if target_user_id == user_id:
        return jsonify({'error': 'Cannot follow yourself'}), 400

    # Update following user's following list
    user_data = user_doc.to_dict()
    if target_user_id not in user_data['following']:
        user_data['following'].append(target_user_id)
        user_doc_ref.update({'following': user_data['following']})
        return jsonify({'success': True})
    
    # If already following, return error
    return jsonify({'error': 'Already following user'}), 400

if __name__ == '__main__':
    app.run(debug=True)



#TODO: make firestore calls atomic
