"""
Arranging fixtures for tests.
"""
import pytest
from unittest.mock import MagicMock, patch
from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config.from_object('config.TestingConfig') 

    with flask_app.test_client() as client:
        yield client

@pytest.fixture
def mock_firestore():
    """Create mocked Firestore client."""
    with patch("app.get_firestore_client") as mock_client:
        mock_db = MagicMock()
        mock_client.return_value = mock_db
        yield mock_db




