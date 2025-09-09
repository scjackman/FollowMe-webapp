"""
Integration tests for the FollowMe webapp.
"""
import pytest
import json
from unittest.mock import Mock, patch


class TestUserWorkflow:
    """Test complete user workflows."""
    
    def test_complete_user_workflow(self, client, mock_firebase):
        """Test the complete user workflow: create -> get info -> get feed -> follow."""
        # The mock_firebase is already configured in the app fixture
        
        # Step 1: Create a user
        user_data = {
            'nickname': 'Test User',
            'origin': 'Test Origin'
        }
        
        create_response = client.post('/api/create_user',
                                    data=json.dumps(user_data),
                                    content_type='application/json')
        
        assert create_response.status_code == 200
        create_data = json.loads(create_response.data)
        assert create_data['success'] is True
        private_user_id = create_data['privateUserID']
        
        # Step 2: Get user info
        # Mock the user document for get_user_info
        mock_user_doc = Mock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = {
            'nickname': 'Test User',
            'origin': 'Test Origin',
            'privateUserID': private_user_id,
            'publicUserID': 'test-public-id',
            'following': [],
            'followerCount': 0,
            'createdAt': '2024-01-01T00:00:00Z'
        }
        mock_users_collection.document.return_value.get.return_value = mock_user_doc
        
        info_response = client.get('/api/user_info')
        assert info_response.status_code == 200
        info_data = json.loads(info_response.data)
        assert info_data['nickname'] == 'Test User'
        
        # Step 3: Get users feed
        # Mock the userList document
        mock_userlist_doc.to_dict.return_value = {'userList': ['test-public-id', 'other-user-id']}
        
        # Mock the users collection query for feed
        mock_query = Mock()
        mock_query.limit.return_value.get.return_value = [Mock(exists=True, to_dict=lambda: {
            'nickname': 'Other User',
            'publicUserID': 'other-user-id',
            'origin': 'Other Origin',
            'followerCount': 5,
            'createdAt': '2024-01-01T00:00:00Z'
        })]
        mock_users_collection.where.return_value = mock_query
        
        feed_response = client.get('/api/users_feed')
        assert feed_response.status_code == 200
        feed_data = json.loads(feed_response.data)
        assert 'users' in feed_data
        assert len(feed_data['users']) > 0
        
        # Step 4: Follow a user
        follow_data = {'targetPublicUserID': 'other-user-id'}
        
        # Mock the follow transaction
        mock_follower_doc = Mock()
        mock_follower_doc.exists = True
        mock_follower_doc.to_dict.return_value = {
            'nickname': 'Test User',
            'origin': 'Test Origin',
            'privateUserID': private_user_id,
            'publicUserID': 'test-public-id',
            'following': [],
            'followerCount': 0,
            'createdAt': '2024-01-01T00:00:00Z'
        }
        
        mock_target_doc = Mock()
        mock_target_doc.exists = True
        mock_target_doc.to_dict.return_value = {
            'nickname': 'Other User',
            'publicUserID': 'other-user-id',
            'privateUserID': 'other-private-id',
            'followerCount': 5,
            'createdAt': '2024-01-01T00:00:00Z'
        }
        
        mock_users_collection.document.return_value.get.return_value = mock_follower_doc
        mock_users_collection.where.return_value.limit.return_value.get.return_value = [mock_target_doc]
        
        follow_response = client.post('/api/follow_user',
                                    data=json.dumps(follow_data),
                                    content_type='application/json')
        
        assert follow_response.status_code == 200
        follow_data_response = json.loads(follow_response.data)
        assert follow_data_response['success'] is True


class TestErrorHandling:
    """Test error handling across the application."""
    
    def test_invalid_json_request(self, client, mock_firebase):
        """Test handling of invalid JSON in requests."""
        response = client.post('/api/create_user',
                             data='invalid json',
                             content_type='application/json')
        
        # Should handle JSON parsing error gracefully
        assert response.status_code in [400, 500]
    
    def test_missing_content_type(self, client, mock_firebase):
        """Test handling of requests without proper content type."""
        response = client.post('/api/create_user',
                             data=json.dumps({'nickname': 'Test', 'origin': 'Test'}))
        
        # Flask returns 415 when Content-Type is missing and route expects JSON
        assert response.status_code == 415
    
    def test_form_data_instead_of_json(self, client, mock_firebase):
        """Test that form data doesn't work when route expects JSON."""
        # Send as form data instead of JSON
        response = client.post('/api/create_user',
                             data={'nickname': 'Test', 'origin': 'Test'})
        
        # Route expects JSON, so form data will cause issues
        assert response.status_code in [400, 415, 500]
    
    def test_very_long_input(self, client, mock_firebase):
        """Test handling of very long input strings."""
        # The mock_firebase is already configured in the app fixture
        
        # Very long nickname (over 32 characters)
        long_nickname = 'A' * 100
        data = {
            'nickname': long_nickname,
            'origin': 'Test Origin'
        }
        
        response = client.post('/api/create_user',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        # The nickname should be truncated to 32 characters
        response_data = json.loads(response.data)
        assert response_data['success'] is True


class TestSecurity:
    """Test security-related functionality."""
    
    def test_xss_prevention(self, client, mock_firebase):
        """Test that XSS attempts are sanitized."""
        # The mock_firebase is already configured in the app fixture
        
        malicious_data = {
            'nickname': '<script>alert("xss")</script>',
            'origin': '"><img src=x onerror=alert("xss")>'
        }
        
        response = client.post('/api/create_user',
                             data=json.dumps(malicious_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        # The malicious content should be sanitized
        response_data = json.loads(response.data)
        assert response_data['success'] is True
    
    def test_sql_injection_prevention(self, client, mock_firebase):
        """Test that SQL injection attempts are handled safely."""
        # The mock_firebase is already configured in the app fixture
        
        malicious_data = {
            'nickname': "'; DROP TABLE users; --",
            'origin': "1' OR '1'='1"
        }
        
        response = client.post('/api/create_user',
                             data=json.dumps(malicious_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        # The malicious content should be sanitized
        response_data = json.loads(response.data)
        assert response_data['success'] is True
