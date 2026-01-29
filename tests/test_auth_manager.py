"""
Tests for Authentication Manager Module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from auth_manager import AuthManager


class TestAuthManager:
    """Test suite for AuthManager class."""
    
    def test_initialization(self):
        """Test AuthManager initialization."""
        auth_manager = AuthManager()
        assert auth_manager is not None
    
    @patch('auth_manager.requests.Session')
    def test_get_cookie_success(self, mock_session_class):
        """Test successful cookie retrieval."""
        auth_manager = AuthManager()
        
        # Mock session and response
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.cookies = {'auth_token': 'test_token', 'session': 'test_session'}
        mock_session.post.return_value = mock_response
        
        credentials = {
            'base_url': 'http://test.com',
            'username': 'testuser',
            'password': 'testpass'
        }
        
        cookie = auth_manager.get_cookie(mock_session, credentials)
        
        assert cookie is not None
        assert 'session_id' in cookie
        assert 'auth_token' in cookie
    
    @patch('auth_manager.requests.Session')
    def test_get_cookie_missing_credentials(self, mock_session_class):
        """Test cookie retrieval with missing credentials."""
        auth_manager = AuthManager()
        mock_session = MagicMock()
        
        # Missing password
        credentials = {
            'base_url': 'http://test.com',
            'username': 'testuser'
        }
        
        cookie = auth_manager.get_cookie(mock_session, credentials)
        
        assert cookie is None
    
    @patch('auth_manager.requests.Session')
    def test_get_cookie_auth_failure(self, mock_session_class):
        """Test cookie retrieval with authentication failure."""
        auth_manager = AuthManager()
        
        # Mock failed response
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_session.post.return_value = mock_response
        
        credentials = {
            'base_url': 'http://test.com',
            'username': 'testuser',
            'password': 'wrongpass'
        }
        
        cookie = auth_manager.get_cookie(mock_session, credentials)
        
        assert cookie is None
    
    @patch('auth_manager.requests.Session')
    def test_get_cookie_no_cookies_in_response(self, mock_session_class):
        """Test cookie retrieval when response has no cookies."""
        auth_manager = AuthManager()
        
        # Mock response with empty cookies
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.cookies = {}
        mock_session.post.return_value = mock_response
        
        credentials = {
            'base_url': 'http://test.com',
            'username': 'testuser',
            'password': 'testpass'
        }
        
        cookie = auth_manager.get_cookie(mock_session, credentials)
        
        # Should return mock cookie when no cookies in response
        assert cookie is not None
        assert 'session_id' in cookie
    
    @patch('auth_manager.requests.Session')
    def test_get_cookie_timeout(self, mock_session_class):
        """Test cookie retrieval with timeout."""
        auth_manager = AuthManager()
        
        # Mock timeout exception
        mock_session = MagicMock()
        mock_session.post.side_effect = __import__('requests').exceptions.Timeout('Connection timeout')
        
        credentials = {
            'base_url': 'http://test.com',
            'username': 'testuser',
            'password': 'testpass'
        }
        
        cookie = auth_manager.get_cookie(mock_session, credentials)
        
        assert cookie is None
    
    @patch('auth_manager.requests.Session')
    def test_get_cookie_request_exception(self, mock_session_class):
        """Test cookie retrieval with request exception."""
        auth_manager = AuthManager()
        
        # Mock request exception
        mock_session = MagicMock()
        mock_session.post.side_effect = __import__('requests').exceptions.RequestException('Connection error')
        
        credentials = {
            'base_url': 'http://test.com',
            'username': 'testuser',
            'password': 'testpass'
        }
        
        cookie = auth_manager.get_cookie(mock_session, credentials)
        
        assert cookie is None
    
    def test_generate_session_id(self):
        """Test session ID generation."""
        auth_manager = AuthManager()
        
        session_id1 = auth_manager._generate_session_id('user1')
        session_id2 = auth_manager._generate_session_id('user2')
        
        # Session IDs should be different for different users
        assert session_id1 != session_id2
        # Session IDs should be 16 characters
        assert len(session_id1) == 16
        assert len(session_id2) == 16
    
    def test_create_mock_cookie(self):
        """Test mock cookie creation."""
        auth_manager = AuthManager()
        
        cookie = auth_manager._create_mock_cookie('testuser')
        
        assert cookie is not None
        assert 'session_id' in cookie
        assert 'auth_token' in cookie
        assert 'user' in cookie
        assert cookie['user'] == 'testuser'
    
    def test_validate_cookie_valid(self):
        """Test validation of a valid cookie."""
        auth_manager = AuthManager()
        
        valid_cookie = {
            'session_id': 'test123',
            'auth_token': 'token456'
        }
        
        result = auth_manager.validate_cookie(valid_cookie)
        
        assert result is True
    
    def test_validate_cookie_missing_field(self):
        """Test validation of cookie with missing required field."""
        auth_manager = AuthManager()
        
        invalid_cookie = {
            'auth_token': 'token456'
        }
        
        result = auth_manager.validate_cookie(invalid_cookie)
        
        assert result is False
    
    def test_validate_cookie_none(self):
        """Test validation of None cookie."""
        auth_manager = AuthManager()
        
        result = auth_manager.validate_cookie(None)
        
        assert result is False
    
    @patch('auth_manager.requests.Session')
    def test_refresh_cookie(self, mock_session_class):
        """Test cookie refresh."""
        auth_manager = AuthManager()
        
        # Mock successful refresh
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.cookies = {'new_token': 'refreshed_token'}
        mock_session.post.return_value = mock_response
        
        credentials = {
            'base_url': 'http://test.com',
            'username': 'testuser',
            'password': 'testpass'
        }
        
        old_cookie = {'session_id': 'old123'}
        
        new_cookie = auth_manager.refresh_cookie(mock_session, credentials, old_cookie)
        
        assert new_cookie is not None
        assert 'session_id' in new_cookie
