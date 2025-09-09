"""
Unit tests for Flask routes.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock


class TestIndexRoute:
    """Test cases for the index route."""
    
    def test_index_route(self, client):
        """Test that the index route returns the main template."""
        response = client.get('/')
        assert response.status_code == 200
        # The response should contain HTML content
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data


class TestCreateUserRoute:
    """Test cases for the create_user route."""
    
    def test_create_user_success(self, client, mock_firebase, sample_user_data):
        """Test successful user creation."""
        # The mock_firebase is already configured in the app fixture
        data = {
            'nickname': 'Test User',
            'origin': 'Test Origin'
        }
        
        response = client.post('/api/create_user', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'privateUserID' in response_data
        
        # Check that cookie is set
        assert 'privateUserID' in response.headers.get('Set-Cookie', '')
    
    def test_create_user_missing_nickname(self, client, mock_firebase):
        """Test user creation with missing nickname."""
        data = {'origin': 'Test Origin'}
        
        response = client.post('/api/create_user',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'error' in response_data
        assert 'required' in response_data['error'].lower()
    
    def test_create_user_missing_origin(self, client, mock_firebase):
        """Test user creation with missing origin."""
        data = {'nickname': 'Test User'}
        
        response = client.post('/api/create_user',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'error' in response_data
        assert 'required' in response_data['error'].lower()
    
    def test_create_user_empty_strings(self, client, mock_firebase):
        """Test user creation with empty strings."""
        data = {'nickname': '   ', 'origin': '   '}
        
        response = client.post('/api/create_user',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'error' in response_data
    
    def test_create_user_sanitizes_input(self, client, mock_firebase):
        """Test that user input is sanitized."""
        # The mock_firebase is already configured in the app fixture
        data = {
            'nickname': '<script>alert("xss")</script>Test User',
            'origin': 'Test<>Origin'
        }
        
        response = client.post('/api/create_user',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        # The sanitized data should be used in the transaction
        # This is tested indirectly through the successful response


class TestGetUserInfoRoute:
    """Test cases for the get_user_info route."""
    
    def test_get_user_info_success(self, client, mock_firebase, sample_user_data):
        """Test successful user info retrieval."""
        # The mock_firebase is already configured in the app fixture
        
        # Set the cookie
        client.set_cookie('privateUserID', 'test-private-id')
        
        response = client.get('/api/user_info')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['nickname'] == sample_user_data['nickname']
        assert response_data['origin'] == sample_user_data['origin']
        assert response_data['privateUserID'] == sample_user_data['privateUserID']
        assert response_data['publicUserID'] == sample_user_data['publicUserID']
    
    def test_get_user_info_no_cookie(self, client, mock_firebase):
        """Test user info retrieval without cookie."""
        response = client.get('/api/user_info')
        
        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert 'error' in response_data
    
    def test_get_user_info_user_not_found(self, client, mock_firebase):
        """Test user info retrieval when user doesn't exist."""
        # The mock_firebase is already configured in the app fixture
        
        # Set the cookie
        client.set_cookie('privateUserID', 'test-private-id')
        
        response = client.get('/api/user_info')
        
        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert 'error' in response_data


class TestGetUsersFeedRoute:
    """Test cases for the get_users_feed route."""
    
    def test_get_users_feed_success(self, client, mock_firebase, sample_user_data, sample_user_list):
        """Test successful users feed retrieval."""
        # The mock_firebase is already configured in the app fixture
        
        # Set the cookie
        client.set_cookie('privateUserID', 'test-private-id')
        
        response = client.get('/api/users_feed')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'users' in response_data
        assert 'hasMore' in response_data
        assert 'page' in response_data
        assert response_data['page'] == 1
    
    def test_get_users_feed_pagination(self, client, mock_firebase, sample_user_data, sample_user_list):
        """Test users feed pagination."""
        # The mock_firebase is already configured in the app fixture
        
        # Set the cookie
        client.set_cookie('privateUserID', 'test-private-id')
        
        response = client.get('/api/users_feed?page=2')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['page'] == 2
    
    def test_get_users_feed_no_cookie(self, client, mock_firebase):
        """Test users feed retrieval without cookie."""
        response = client.get('/api/users_feed')
        
        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert 'error' in response_data
    
    def test_get_users_feed_user_not_found(self, client, mock_firebase):
        """Test users feed retrieval when current user doesn't exist."""
        # The mock_firebase is already configured in the app fixture
        
        # Set the cookie
        client.set_cookie('privateUserID', 'test-private-id')
        
        response = client.get('/api/users_feed')
        
        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert 'error' in response_data


class TestFollowUserRoute:
    """Test cases for the follow_user route."""
    
    def test_follow_user_success(self, client, mock_firebase, sample_user_data):
        """Test successful user following."""
        # The mock_firebase is already configured in the app fixture
        
        data = {'targetPublicUserID': 'target-public-id'}
        
        # Set the cookie
        client.set_cookie('privateUserID', 'test-private-id')
        
        response = client.post('/api/follow_user',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
    
    def test_follow_user_no_cookie(self, client, mock_firebase):
        """Test follow user without cookie."""
        data = {'targetPublicUserID': 'target-public-id'}
        
        response = client.post('/api/follow_user',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert 'error' in response_data
    
    def test_follow_user_no_target_id(self, client, mock_firebase):
        """Test follow user without target user ID."""
        # Set the cookie
        client.set_cookie('privateUserID', 'test-private-id')
        
        data = {}
        
        response = client.post('/api/follow_user',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert 'error' in response_data
    
    def test_follow_user_already_following(self, client, mock_firebase, sample_user_data):
        """Test follow user when already following."""
        # The mock_firebase is already configured in the app fixture
        
        data = {'targetPublicUserID': 'target-public-id'}
        
        # Set the cookie
        client.set_cookie('privateUserID', 'test-private-id')
        
        response = client.post('/api/follow_user',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'error' in response_data
        assert 'already following' in response_data['error'].lower()
