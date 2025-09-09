"""
Pytest configuration and fixtures for the FollowMe webapp tests.
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from flask import Flask

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """Create a test Flask application."""
    # Set test environment
    os.environ['APP_SETTINGS'] = 'config.DevelopmentConfig'
    
    # Mock Firebase initialization BEFORE importing the app
    with patch('firebase_config.initialise_firebase'), \
         patch('firebase_config.get_firestore_client') as mock_get_client:
        
        # Create mock Firestore client
        mock_db = Mock()
        mock_get_client.return_value = mock_db
        
        # Mock collections and documents
        mock_users_collection = Mock()
        mock_userlist_doc = Mock()
        mock_user_doc = Mock()
        
        # Configure mock document behavior
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = {
            'nickname': 'Test User',
            'origin': 'Test Origin',
            'privateUserID': 'test-private-id',
            'publicUserID': 'test-public-id',
            'following': [],
            'followerCount': 0,
            'createdAt': '2024-01-01T00:00:00Z'
        }
        
        mock_userlist_doc.exists = True
        mock_userlist_doc.to_dict.return_value = {'userList': ['test-public-id']}
        
        # Configure the collection to return the mock document when .document().get() is called
        mock_users_collection.document.return_value = mock_user_doc
        mock_users_collection.where.return_value.limit.return_value.get.return_value = [mock_user_doc]
        
        mock_db.collection.return_value = mock_users_collection
        mock_db.transaction.return_value = Mock()
        
        # Now import the app with mocked Firebase
        from app import app as flask_app
        
        # Configure the app for testing
        flask_app.config['TESTING'] = True
        flask_app.config['DEBUG'] = True
        
        # Set up the mock for the global db variable and collections
        with patch('app.db', mock_db), \
             patch('app.USERS_COLLECTION', mock_users_collection), \
             patch('app.USERLIST_DOC', mock_userlist_doc):
            yield flask_app


@pytest.fixture
def sanitise_input():
    """Import sanitise_input function for testing."""
    from app import sanitise_input
    return sanitise_input


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def mock_firebase(app):
    """Mock Firebase/Firestore for testing."""
    # The Firebase mocking is now handled in the app fixture
    # This fixture provides access to the mock for individual tests
    from app import db
    return db


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'nickname': 'Test User',
        'origin': 'Test Origin',
        'privateUserID': 'test-private-id',
        'publicUserID': 'test-public-id',
        'following': [],
        'followerCount': 0,
        'createdAt': '2024-01-01T00:00:00Z'
    }


@pytest.fixture
def sample_user_list():
    """Sample user list for testing."""
    return ['user1-public-id', 'user2-public-id', 'test-public-id']
