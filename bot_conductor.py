"""
Bot Conductor Module

Manages concurrent data extraction tasks from Phoenix by coordinating multiple bot instances.
"""

import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from phoenix_bot import PhoenixBot
from data_validator import DataValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BotConductor:
    """
    Orchestrates multiple bot instances for concurrent data extraction from Phoenix.
    
    Responsibilities:
    - Divide PRI lists into batches
    - Manage multiple bot instances
    - Handle authentication
    - Oversee data extraction
    - Validate results
    """
    
    def __init__(self, max_workers: int = 5, batch_size: int = 30):
        """
        Initialize the Bot Conductor.
        
        Args:
            max_workers: Maximum number of concurrent bot instances
            batch_size: Maximum number of PRIs per batch (default: 30)
        """
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.validator = DataValidator()
        self.results_lock = Lock()
        logger.info(f"BotConductor initialized with {max_workers} workers and batch size {batch_size}")
    
    def divide_pris(self, pri_list: List[str]) -> List[List[str]]:
        """
        Divide PRI list into batches of up to batch_size PRIs.
        
        Args:
            pri_list: List of PRIs to divide
            
        Returns:
            List of PRI batches
        """
        if not pri_list:
            logger.warning("Empty PRI list provided")
            return []
        
        batches = []
        for i in range(0, len(pri_list), self.batch_size):
            batch = pri_list[i:i + self.batch_size]
            batches.append(batch)
            logger.debug(f"Created batch {len(batches)} with {len(batch)} PRIs")
        
        logger.info(f"Divided {len(pri_list)} PRIs into {len(batches)} batches")
        return batches
    
    def extract_data(
        self,
        pri_list: List[str],
        phoenix_credentials: Dict[str, str],
        query_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract data from Phoenix using multiple concurrent bots.
        
        Args:
            pri_list: List of PRIs to extract data for
            phoenix_credentials: Phoenix authentication credentials
            query_template: Optional custom query template
            
        Returns:
            Dictionary containing extraction results and metadata
        """
        logger.info(f"Starting data extraction for {len(pri_list)} PRIs")
        
        # Divide PRIs into batches
        batches = self.divide_pris(pri_list)
        
        if not batches:
            return {
                'status': 'error',
                'message': 'No PRIs to process',
                'results': [],
                'failed': []
            }
        
        # Initialize result storage
        all_results = []
        failed_pris = []
        
        # Process batches concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit batch processing tasks
            future_to_batch = {}
            for batch_idx, batch in enumerate(batches):
                future = executor.submit(
                    self._process_batch,
                    batch,
                    batch_idx,
                    phoenix_credentials,
                    query_template
                )
                future_to_batch[future] = (batch_idx, batch)
            
            # Collect results as they complete
            for future in as_completed(future_to_batch):
                batch_idx, batch = future_to_batch[future]
                try:
                    batch_results = future.result()
                    
                    # Thread-safe result aggregation
                    with self.results_lock:
                        all_results.extend(batch_results['results'])
                        failed_pris.extend(batch_results['failed'])
                    
                    logger.info(
                        f"Batch {batch_idx + 1}/{len(batches)} completed: "
                        f"{len(batch_results['results'])} successful, "
                        f"{len(batch_results['failed'])} failed"
                    )
                    
                except Exception as e:
                    logger.error(f"Batch {batch_idx + 1} failed with error: {str(e)}")
                    with self.results_lock:
                        failed_pris.extend(batch)
        
        # Compile final results
        result_summary = {
            'status': 'completed',
            'total_pris': len(pri_list),
            'successful': len(all_results),
            'failed': len(failed_pris),
            'results': all_results,
            'failed_pris': failed_pris
        }
        
        logger.info(
            f"Data extraction completed: {result_summary['successful']}/{result_summary['total_pris']} successful"
        )
        
        return result_summary
    
    def _process_batch(
        self,
        batch: List[str],
        batch_idx: int,
        phoenix_credentials: Dict[str, str],
        query_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a single batch of PRIs using a bot instance.
        
        Args:
            batch: List of PRIs in this batch
            batch_idx: Index of the batch
            phoenix_credentials: Phoenix credentials
            query_template: Optional query template
            
        Returns:
            Dictionary containing batch results
        """
        logger.info(f"Processing batch {batch_idx + 1} with {len(batch)} PRIs")
        
        # Create bot instance for this batch
        bot = PhoenixBot(
            credentials=phoenix_credentials,
            batch_id=batch_idx
        )
        
        try:
            # Authenticate bot
            if not bot.authenticate():
                logger.error(f"Batch {batch_idx + 1}: Authentication failed")
                return {'results': [], 'failed': batch}
            
            logger.info(f"Batch {batch_idx + 1}: Authentication successful")
            
            # Extract data for batch
            batch_results = bot.extract_batch_data(batch, query_template)
            
            return batch_results
            
        except Exception as e:
            logger.error(f"Batch {batch_idx + 1}: Error during processing: {str(e)}")
            return {'results': [], 'failed': batch}
        
        finally:
            # Clean up bot resources
            bot.cleanup()
    
    def validate_results(
        self,
        results: Dict[str, Any],
        sample_pris: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate extraction results for quality and completeness.
        
        Args:
            results: Extraction results to validate
            sample_pris: Optional list of sample PRIs for detailed validation
            
        Returns:
            Validation report
        """
        logger.info("Starting result validation")
        
        validation_report = self.validator.validate(
            results=results,
            sample_pris=sample_pris
        )
        
        logger.info(
            f"Validation completed: "
            f"{validation_report['valid_count']}/{validation_report['total_count']} records valid"
        )
        
        return validation_report
    
    def get_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate statistics from extraction results.
        
        Args:
            results: Extraction results
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'total_pris_processed': results.get('total_pris', 0),
            'successful_extractions': results.get('successful', 0),
            'failed_extractions': results.get('failed', 0),
            'success_rate': 0.0
        }
        
        if stats['total_pris_processed'] > 0:
            stats['success_rate'] = (
                stats['successful_extractions'] / stats['total_pris_processed'] * 100
            )
        
        return stats
