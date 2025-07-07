import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

def initialise_firebase():
    """Initialize Firebase Admin SDK with credentials from environment variables"""
    try:
        # Check if Firebase app is already initialized
        if not firebase_admin._apps:

            # Get the path to the service account key file
            cred = credentials.Certificate("serviceAccountKey.json")
            
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