from flask import Flask, render_template, request, jsonify, make_response
import uuid
from firebase_config import initialize_firebase

app = Flask(__name__)

# Initialize Firebase on app startup
initialize_firebase()

# Simulated in-memory DB for users and userList
users_db = {}
user_list = []

# Create a list of n users with a random origin
def create_users(n):
    for i in range(n):
        user_id = str(uuid.uuid4())
        user_obj = {
            'nickname': f'User {i}',
            'origin': f'Origin {i}',
            'userID': user_id,
            'following': []
        }
        users_db[user_id] = user_obj
        user_list.append(user_id)   

create_users(150)
            
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/create_user', methods=['POST'])
def create_user():
    # Get the nickname and origin from the request and return an error if they are not provided
    data = request.get_json()
    nickname = data.get('nickname', '').strip()
    origin = data.get('origin', '').strip()
    if not nickname or not origin:
        return jsonify({'error': 'Nickname and origin are required.'}), 400

    # Create a new user object with a unique userID and add it to the users_db and user_list
    user_id = str(uuid.uuid4())
    user_obj = {
        'nickname': nickname,
        'origin': origin,
        'userID': user_id,
        'following': []
    }
    users_db[user_id] = user_obj
    user_list.append(user_id)

    # Return a response with the userID and a cookie set with the userID
    resp = make_response(jsonify({'success': True, 'userID': user_id}))
    resp.set_cookie('userID', user_id, max_age=60*60*24*365) # 1 year expiration
    return resp

# Get the user info for the current user
@app.route('/api/user_info')
def get_user_info():
    # Get the userID from the cookie and return an error if the userID is not found
    user_id = request.cookies.get('userID')
    if not user_id or user_id not in users_db:
        return jsonify({'error': 'User not found'}), 404
    
    user = users_db[user_id]
    return jsonify({
        'nickname': user['nickname'],
        'userID': user['userID'],
        'following': user['following']
    })

# Get the users feed for the current user
@app.route('/api/users_feed')
def get_users_feed():
    # Get the userID from the cookie and return an error if the userID is not found
    user_id = request.cookies.get('userID')
    if not user_id or user_id not in users_db:
        return jsonify({'error': 'User not found'}), 404
    
    # Get the page number from the request and set the default page to 1
    page = int(request.args.get('page', 1))
    per_page = 10
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Get paginated user IDs, excluding the current user
    user_ids = [uid for uid in user_list if uid != user_id][start_idx:end_idx]
    
    # Get user objects for the feed
    feed_users = []
    for uid in user_ids:
        user = users_db[uid]
        feed_users.append({
            'nickname': user['nickname'],
            'userID': user['userID'],
            'origin': user.get('origin', ''),
            'isFollowing': uid in users_db[user_id]['following']
        })
    
    has_more = end_idx < len([uid for uid in user_list if uid != user_id])
    
    return jsonify({
        'users': feed_users,
        'hasMore': has_more,
        'page': page
    })

@app.route('/api/follow_user', methods=['POST'])
def follow_user():
    user_id = request.cookies.get('userID')
    if not user_id or user_id not in users_db:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    target_user_id = data.get('targetUserID')
    
    if not target_user_id or target_user_id not in users_db:
        return jsonify({'error': 'Target user not found'}), 404
    
    if target_user_id == user_id:
        return jsonify({'error': 'Cannot follow yourself'}), 400
    
    # Add to following list if not already following
    if target_user_id not in users_db[user_id]['following']:
        users_db[user_id]['following'].append(target_user_id)
        return jsonify({'success': True})

    return jsonify({'error': 'Already following user'}), 400

if __name__ == '__main__':
    app.run(debug=True)