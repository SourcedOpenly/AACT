"""
Tests for Phoenix Bot Module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from phoenix_bot import PhoenixBot


class TestPhoenixBot:
    """Test suite for PhoenixBot class."""
    
    def test_initialization(self):
        """Test PhoenixBot initialization."""
        credentials = {'base_url': 'http://test.com', 'username': 'test', 'password': 'pass'}
        bot = PhoenixBot(credentials=credentials, batch_id=1)
        
        assert bot.credentials == credentials
        assert bot.batch_id == 1
        assert bot.authenticated is False
        assert bot.cookie is None
    
    @patch('phoenix_bot.AuthManager')
    def test_authenticate_success(self, mock_auth_manager_class):
        """Test successful authentication."""
        # Mock auth manager
        mock_auth_manager = MagicMock()
        mock_auth_manager.get_cookie.return_value = {'session_id': 'test123', 'auth_token': 'token456'}
        mock_auth_manager_class.return_value = mock_auth_manager
        
        credentials = {'base_url': 'http://test.com', 'username': 'test', 'password': 'pass'}
        bot = PhoenixBot(credentials=credentials, batch_id=1)
        
        result = bot.authenticate()
        
        assert result is True
        assert bot.authenticated is True
        assert bot.cookie is not None
    
    @patch('phoenix_bot.AuthManager')
    def test_authenticate_failure(self, mock_auth_manager_class):
        """Test authentication failure."""
        # Mock auth manager returning None
        mock_auth_manager = MagicMock()
        mock_auth_manager.get_cookie.return_value = None
        mock_auth_manager_class.return_value = mock_auth_manager
        
        credentials = {'base_url': 'http://test.com', 'username': 'test', 'password': 'pass'}
        bot = PhoenixBot(credentials=credentials, batch_id=1)
        
        result = bot.authenticate()
        
        assert result is False
        assert bot.authenticated is False
    
    def test_extract_batch_data_not_authenticated(self):
        """Test extraction without authentication."""
        credentials = {'base_url': 'http://test.com', 'username': 'test', 'password': 'pass'}
        bot = PhoenixBot(credentials=credentials, batch_id=1)
        
        result = bot.extract_batch_data(['PRI001', 'PRI002'])
        
        assert result['results'] == []
        assert result['failed'] == ['PRI001', 'PRI002']
    
    @patch('phoenix_bot.AuthManager')
    def test_extract_batch_data_success(self, mock_auth_manager_class):
        """Test successful data extraction."""
        # Setup authenticated bot
        mock_auth_manager = MagicMock()
        mock_auth_manager.get_cookie.return_value = {'session_id': 'test123'}
        mock_auth_manager_class.return_value = mock_auth_manager
        
        credentials = {'base_url': 'http://test.com', 'username': 'test', 'password': 'pass'}
        bot = PhoenixBot(credentials=credentials, batch_id=1)
        bot.authenticate()
        
        # Mock query responses
        with patch.object(bot, '_query_phoenix') as mock_query:
            mock_query.side_effect = [
                {'field1': 'value1'},
                {'field2': 'value2'}
            ]
            
            result = bot.extract_batch_data(['PRI001', 'PRI002'])
            
            assert len(result['results']) == 2
            assert len(result['failed']) == 0
            assert result['results'][0]['pri'] == 'PRI001'
            assert result['results'][1]['pri'] == 'PRI002'
    
    @patch('phoenix_bot.AuthManager')
    def test_extract_batch_data_partial_failure(self, mock_auth_manager_class):
        """Test extraction with some failures."""
        # Setup authenticated bot
        mock_auth_manager = MagicMock()
        mock_auth_manager.get_cookie.return_value = {'session_id': 'test123'}
        mock_auth_manager_class.return_value = mock_auth_manager
        
        credentials = {'base_url': 'http://test.com', 'username': 'test', 'password': 'pass'}
        bot = PhoenixBot(credentials=credentials, batch_id=1)
        bot.authenticate()
        
        # Mock query responses with one failure
        with patch.object(bot, '_query_phoenix') as mock_query:
            mock_query.side_effect = [
                {'field1': 'value1'},
                None,  # Failed query
                {'field3': 'value3'}
            ]
            
            result = bot.extract_batch_data(['PRI001', 'PRI002', 'PRI003'])
            
            assert len(result['results']) == 2
            assert len(result['failed']) == 1
            assert 'PRI002' in result['failed']
    
    def test_get_session_info(self):
        """Test getting session info."""
        credentials = {'base_url': 'http://test.com', 'username': 'test', 'password': 'pass'}
        bot = PhoenixBot(credentials=credentials, batch_id=5)
        
        info = bot.get_session_info()
        
        assert info['batch_id'] == 5
        assert info['authenticated'] is False
        assert info['has_cookie'] is False
        assert info['base_url'] == 'http://test.com'
    
    def test_cleanup(self):
        """Test resource cleanup."""
        credentials = {'base_url': 'http://test.com', 'username': 'test', 'password': 'pass'}
        bot = PhoenixBot(credentials=credentials, batch_id=1)
        
        # Should not raise any exceptions
        bot.cleanup()
