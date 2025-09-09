"""
Test helper functions and utilities.
"""
import pytest
from unittest.mock import Mock, patch
import json


class TestFirebaseMocking:
    """Test Firebase mocking utilities."""
    
    def test_mock_firebase_initialization(self, mock_firebase):
        """Test that Firebase mocking works correctly."""
        assert mock_firebase is not None
        assert hasattr(mock_firebase, 'collection')
        assert hasattr(mock_firebase, 'transaction')
    
    def test_mock_firebase_collection_access(self, mock_firebase):
        """Test accessing Firestore collections through mock."""
        mock_collection = mock_firebase.collection('users')
        assert mock_collection is not None
    
    def test_mock_firebase_transaction(self, mock_firebase):
        """Test Firestore transaction mocking."""
        mock_transaction = mock_firebase.transaction()
        assert mock_transaction is not None


class TestSampleData:
    """Test sample data fixtures."""
    
    def test_sample_user_data_structure(self, sample_user_data):
        """Test that sample user data has correct structure."""
        required_fields = [
            'nickname', 'origin', 'privateUserID', 'publicUserID',
            'following', 'followerCount', 'createdAt'
        ]
        
        for field in required_fields:
            assert field in sample_user_data
        
        assert isinstance(sample_user_data['following'], list)
        assert isinstance(sample_user_data['followerCount'], int)
        assert sample_user_data['followerCount'] >= 0
    
    def test_sample_user_list_structure(self, sample_user_list):
        """Test that sample user list has correct structure."""
        assert isinstance(sample_user_list, list)
        assert len(sample_user_list) > 0
        
        # All items should be strings (public user IDs)
        for user_id in sample_user_list:
            assert isinstance(user_id, str)
            assert len(user_id) > 0


class TestClientHelpers:
    """Test client helper functions."""
    
    def test_client_cookie_setting(self, client):
        """Test setting cookies on the test client."""
        client.set_cookie('privateUserID', 'test-id')
        
        # Test that we can make a request with the cookie
        response = client.get('/api/user_info')
        # Should get 404 because user doesn't exist, but cookie should be present
        assert response.status_code == 404
    
    def test_client_json_request(self, client):
        """Test making JSON requests with the test client."""
        data = {'test': 'data'}
        response = client.post('/api/create_user',
                             data=json.dumps(data),
                             content_type='application/json')
        
        # Should get 400 because required fields are missing, but request should be processed
        assert response.status_code == 400


class TestResponseValidation:
    """Test response validation helpers."""
    
    def test_json_response_validation(self, client, mock_firebase):
        """Test validation of JSON responses."""
        # The mock_firebase is already configured in the app fixture
        # We just need to test that the response is valid JSON
        
        data = {'nickname': 'Test', 'origin': 'Test'}
        response = client.post('/api/create_user',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert isinstance(response_data, dict)
        assert 'success' in response_data
    
    def test_error_response_validation(self, client):
        """Test validation of error responses."""
        response = client.get('/api/user_info')
        
        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert isinstance(response_data, dict)
        assert 'error' in response_data
        assert isinstance(response_data['error'], str)
        assert len(response_data['error']) > 0


class TestMockDataGeneration:
    """Test mock data generation utilities."""
    
    def test_generate_mock_user_data(self):
        """Test generating mock user data."""
        from tests.conftest import sample_user_data
        
        # This should be available as a fixture
        assert sample_user_data is not None
    
    def test_generate_mock_user_list(self):
        """Test generating mock user list."""
        from tests.conftest import sample_user_list
        
        # This should be available as a fixture
        assert sample_user_list is not None
    
    def test_mock_data_consistency(self, sample_user_data, sample_user_list):
        """Test that mock data is consistent."""
        # The sample user's public ID should be in the user list
        assert sample_user_data['publicUserID'] in sample_user_list
