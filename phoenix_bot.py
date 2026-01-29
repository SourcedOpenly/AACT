"""
Phoenix Bot Module

Individual bot implementation for extracting data from Phoenix.
"""

import logging
import time
from typing import List, Dict, Any, Optional

import requests

from auth_manager import AuthManager

logger = logging.getLogger(__name__)


class PhoenixBot:
    """
    Individual bot instance for data extraction from Phoenix.
    
    Each bot:
    - Authenticates with Phoenix
    - Executes queries for a batch of PRIs
    - Collects and formats results
    """
    
    def __init__(self, credentials: Dict[str, str], batch_id: int):
        """
        Initialize a Phoenix bot.
        
        Args:
            credentials: Phoenix authentication credentials
            batch_id: Unique identifier for this bot's batch
        """
        self.credentials = credentials
        self.batch_id = batch_id
        self.session = requests.Session()
        self.auth_manager = AuthManager()
        self.authenticated = False
        self.cookie = None
        
        logger.info(f"PhoenixBot {batch_id} initialized")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Phoenix and obtain a unique session cookie.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            logger.info(f"Bot {self.batch_id}: Attempting authentication")
            
            # Get authentication cookie
            self.cookie = self.auth_manager.get_cookie(
                session=self.session,
                credentials=self.credentials
            )
            
            if not self.cookie:
                logger.error(f"Bot {self.batch_id}: Failed to obtain authentication cookie")
                return False
            
            # Set cookie in session
            self.session.cookies.update(self.cookie)
            self.authenticated = True
            
            logger.info(f"Bot {self.batch_id}: Authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Bot {self.batch_id}: Authentication error: {str(e)}")
            return False
    
    def extract_batch_data(
        self,
        pri_batch: List[str],
        query_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract data for a batch of PRIs from Phoenix.
        
        Args:
            pri_batch: List of PRIs to extract data for
            query_template: Optional custom query template
            
        Returns:
            Dictionary containing results and failed PRIs
        """
        if not self.authenticated:
            logger.error(f"Bot {self.batch_id}: Cannot extract data - not authenticated")
            return {'results': [], 'failed': pri_batch}
        
        logger.info(f"Bot {self.batch_id}: Extracting data for {len(pri_batch)} PRIs")
        
        results = []
        failed = []
        
        for pri in pri_batch:
            try:
                # Execute Phoenix query for this PRI
                data = self._query_phoenix(pri, query_template)
                
                if data:
                    results.append({
                        'pri': pri,
                        'data': data,
                        'timestamp': time.time(),
                        'bot_id': self.batch_id
                    })
                    logger.debug(f"Bot {self.batch_id}: Successfully extracted data for {pri}")
                else:
                    failed.append(pri)
                    logger.warning(f"Bot {self.batch_id}: No data found for {pri}")
                    
            except Exception as e:
                failed.append(pri)
                logger.error(f"Bot {self.batch_id}: Error extracting {pri}: {str(e)}")
        
        logger.info(
            f"Bot {self.batch_id}: Extraction complete - "
            f"{len(results)} successful, {len(failed)} failed"
        )
        
        return {'results': results, 'failed': failed}
    
    def _query_phoenix(
        self,
        pri: str,
        query_template: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a Phoenix query for a specific PRI.
        
        Args:
            pri: PRI identifier
            query_template: Optional custom query template
            
        Returns:
            Query results or None if failed
        """
        try:
            # Build query URL
            base_url = self.credentials.get('base_url', 'https://phoenix.example.com')
            
            # Default query endpoint and parameters
            if query_template:
                query_url = f"{base_url}/query"
                params = {'template': query_template, 'pri': pri}
            else:
                # Default query structure
                query_url = f"{base_url}/api/data"
                params = {'pri': pri, 'format': 'json'}
            
            # Execute query with authentication
            response = self.session.get(
                query_url,
                params=params,
                timeout=30
            )
            
            # Check response
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.warning(
                    f"Bot {self.batch_id}: Query failed for {pri} "
                    f"with status {response.status_code}"
                )
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Bot {self.batch_id}: Query timeout for {pri}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Bot {self.batch_id}: Query error for {pri}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Bot {self.batch_id}: Unexpected error querying {pri}: {str(e)}")
            return None
    
    def cleanup(self):
        """
        Clean up bot resources and close session.
        """
        try:
            self.session.close()
            logger.info(f"Bot {self.batch_id}: Resources cleaned up")
        except Exception as e:
            logger.error(f"Bot {self.batch_id}: Error during cleanup: {str(e)}")
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about the bot's session.
        
        Returns:
            Session information dictionary
        """
        return {
            'batch_id': self.batch_id,
            'authenticated': self.authenticated,
            'has_cookie': self.cookie is not None,
            'base_url': self.credentials.get('base_url', 'N/A')
        }
