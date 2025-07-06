import os
from firebase_admin import credentials, firestore

def initialize_firebase():
    """Initialize Firebase Admin SDK with credentials from environment variables"""
    try:
        # Check if Firebase app is already initialized
        if not firebase_admin._apps:
            # Get required environment variables
            project_id = os.environ.get('FIREBASE_PROJECT_ID')
            private_key = os.environ.get('FIREBASE_PRIVATE_KEY')
            client_email = os.environ.get('FIREBASE_CLIENT_EMAIL')
            
            # Validate required environment variables
            if not all([project_id, private_key, client_email]):
                raise ValueError("Missing required environment variables: FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, FIREBASE_CLIENT_EMAIL")
            
            # Handle private key formatting
            private_key = private_key.strip('"').replace('\\n', '\n')
            
            # Create credentials from env variables
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": project_id,
                "private_key": private_key,
                "client_email": client_email
            })
            
            # Initialize Firebase app 
            firebase_admin.initialize_app(cred)
            
            print("Firebase initialized successfully")
        else:
            print("Firebase already initialized")
            
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        raise

def get_firestore_client():
    """Get Firestore client instance"""
    try:
        db = firestore.client()
        return db
    except Exception as e:
        print(f"Error getting Firestore client: {e}")
        raise