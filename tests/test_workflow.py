'''
Test full user workflow through app.
'''

import pytest

def test_add_user(client,mock_firestore):
    assert mock_firestore is not None

    # Arrange
    mock_users_collection = mock_firestore.collection.return_value
    mock_userlist_doc_ref = mock_users_collection.document.return_value
    mock_userlist_doc_ref.set.return_value = {'success': True, 'privateUserID': 'private-user-id'}  # pretend it succeeds

    # Act
    response = client.post('/api/create_user', json={'nickname': 'Sam', 'origin': 'Vancouver'})

    # Assert
    mock_firestore.collection.assert_called_once_with('users')
    mock_users_collection.document.assert_called_once_with('userList')
    mock_userlist_doc_ref.set.assert_called_once_with({'nickname': 'Sam', 'origin': 'Vancouver'})
    assert response.json == {'success': True, 'privateUserID': 'private-user-id'}