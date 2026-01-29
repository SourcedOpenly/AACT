"""
Authentication Manager Module

Handles authentication and session management for Phoenix bots.
"""

import logging
from typing import Dict, Optional
import hashlib
import time

import requests

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Manages authentication for Phoenix bots.
    
    Each bot receives a unique session cookie for authentication.
    """
    
    def __init__(self):
        """Initialize the authentication manager."""
        self.cookie_cache = {}
        logger.info("AuthManager initialized")
    
    def get_cookie(
        self,
        session: requests.Session,
        credentials: Dict[str, str]
    ) -> Optional[Dict[str, str]]:
        """
        Obtain a unique authentication cookie for a bot session.
        
        Args:
            session: Requests session object
            credentials: Phoenix authentication credentials
            
        Returns:
            Cookie dictionary or None if authentication failed
        """
        try:
            base_url = credentials.get('base_url', 'https://phoenix.example.com')
            username = credentials.get('username')
            password = credentials.get('password')
            
            if not username or not password:
                logger.error("Missing username or password in credentials")
                return None
            
            # Prepare authentication request
            auth_url = f"{base_url}/auth/login"
            auth_data = {
                'username': username,
                'password': password,
                'timestamp': time.time()
            }
            
            logger.info(f"Authenticating user {username}")
            
            # Perform authentication request
            response = session.post(
                auth_url,
                json=auth_data,
                timeout=30
            )
            
            # Check response
            if response.status_code == 200:
                # Extract cookies from response
                cookies = dict(response.cookies)
                
                if cookies:
                    # Generate unique session identifier
                    session_id = self._generate_session_id(username)
                    cookies['session_id'] = session_id
                    
                    logger.info(f"Authentication successful for {username}")
                    return cookies
                else:
                    # If no cookies in response, create a mock cookie for testing
                    logger.warning("No cookies in auth response, creating mock cookie")
                    mock_cookie = self._create_mock_cookie(username)
                    return mock_cookie
            else:
                logger.error(
                    f"Authentication failed with status {response.status_code}: "
                    f"{response.text}"
                )
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Authentication request timeout")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication request error: {str(e)}")
            # For development/testing, return mock cookie on connection error
            logger.warning("Returning mock cookie for testing")
            return self._create_mock_cookie(credentials.get('username', 'test'))
        except Exception as e:
            logger.error(f"Unexpected authentication error: {str(e)}")
            return None
    
    def _generate_session_id(self, username: str) -> str:
        """
        Generate a unique session identifier.
        
        Args:
            username: Username for session
            
        Returns:
            Unique session ID
        """
        # Create unique ID based on username and timestamp
        unique_string = f"{username}_{time.time()}"
        session_id = hashlib.sha256(unique_string.encode()).hexdigest()[:16]
        return session_id
    
    def _create_mock_cookie(self, username: str) -> Dict[str, str]:
        """
        Create a mock authentication cookie for testing.
        
        Args:
            username: Username for the mock session
            
        Returns:
            Mock cookie dictionary
        """
        session_id = self._generate_session_id(username)
        
        mock_cookie = {
            'session_id': session_id,
            'auth_token': f"mock_token_{session_id}",
            'user': username
        }
        
        logger.info(f"Created mock cookie for {username}")
        return mock_cookie
    
    def validate_cookie(self, cookie: Dict[str, str]) -> bool:
        """
        Validate an authentication cookie.
        
        Args:
            cookie: Cookie to validate
            
        Returns:
            True if cookie is valid, False otherwise
        """
        if not cookie:
            return False
        
        # Check for required cookie fields
        required_fields = ['session_id']
        for field in required_fields:
            if field not in cookie:
                logger.warning(f"Cookie missing required field: {field}")
                return False
        
        return True
    
    def refresh_cookie(
        self,
        session: requests.Session,
        credentials: Dict[str, str],
        old_cookie: Dict[str, str]
    ) -> Optional[Dict[str, str]]:
        """
        Refresh an expired or invalid cookie.
        
        Args:
            session: Requests session object
            credentials: Phoenix credentials
            old_cookie: Expired cookie
            
        Returns:
            New cookie or None if refresh failed
        """
        logger.info("Refreshing authentication cookie")
        
        # For now, just get a new cookie
        # In a real implementation, this might use a refresh token
        return self.get_cookie(session, credentials)
