# Testing Guide for FollowMe Webapp

This document explains how to run and understand the tests for the FollowMe webapp.

## Test Structure

```
tests/
├── __init__.py              # Test package marker
├── conftest.py              # Pytest configuration and fixtures
├── test_utils.py            # Tests for utility functions
├── test_routes.py           # Tests for Flask routes
├── test_integration.py      # Integration tests and workflows
└── test_helpers.py          # Test helper functions and utilities
```

## Test Categories

### 1. Unit Tests (`test_utils.py`)
- **sanitise_input()** function tests
- Input validation and sanitization
- Edge cases and security testing

### 2. Route Tests (`test_routes.py`)
- **GET /** - Index route
- **POST /api/create_user** - User creation
- **GET /api/user_info** - User information retrieval
- **GET /api/users_feed** - Users feed with pagination
- **POST /api/follow_user** - User following functionality

### 3. Integration Tests (`test_integration.py`)
- Complete user workflows
- End-to-end scenarios
- Error handling across components
- Security testing (XSS, injection prevention)

### 4. Helper Tests (`test_helpers.py`)
- Test fixtures and utilities
- Mock data validation
- Client helper functions

## Running Tests

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
# Using pytest directly
pytest

# Using the test runner script
python run_tests.py

# With coverage report
pytest --cov=app --cov-report=html
```

### Run Specific Test Files
```bash
# Test only utility functions
pytest tests/test_utils.py

# Test only routes
pytest tests/test_routes.py

# Test only integration tests
pytest tests/test_integration.py
```

### Run Specific Test Classes or Functions
```bash
# Test specific class
pytest tests/test_routes.py::TestCreateUserRoute

# Test specific function
pytest tests/test_utils.py::TestSanitiseInput::test_sanitise_input_removes_html_tags
```

## Test Configuration

### pytest.ini
- Test discovery patterns
- Coverage settings (minimum 80%)
- Output formatting
- HTML coverage reports in `htmlcov/`

### Fixtures (conftest.py)
- **app**: Flask test application
- **client**: Test client for making requests
- **mock_firebase**: Mocked Firebase/Firestore
- **sample_user_data**: Test user data
- **sample_user_list**: Test user list

## Mocking Strategy

### Firebase/Firestore Mocking
- All Firebase operations are mocked to avoid external dependencies
- Firestore collections, documents, and transactions are simulated
- No actual Firebase credentials required for testing

### Request/Response Mocking
- Flask test client handles HTTP requests
- Cookies and headers are properly simulated
- JSON request/response handling

## Coverage

The test suite aims for 80%+ code coverage:
- All routes and their error conditions
- Utility functions with edge cases
- Input validation and sanitization
- Security-related functionality

## Test Data

### Sample User Data
```python
{
    'nickname': 'Test User',
    'origin': 'Test Origin',
    'privateUserID': 'test-private-id',
    'publicUserID': 'test-public-id',
    'following': [],
    'followerCount': 0,
    'createdAt': '2024-01-01T00:00:00Z'
}
```

### Sample User List
```python
['user1-public-id', 'user2-public-id', 'test-public-id']
```
