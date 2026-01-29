"""
Data Validator Module

Validates extraction results for quality and completeness.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates data extraction results.
    
    Performs quality checks and validates sample PRIs.
    """
    
    def __init__(self):
        """Initialize the data validator."""
        logger.info("DataValidator initialized")
    
    def validate(
        self,
        results: Dict[str, Any],
        sample_pris: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate extraction results.
        
        Args:
            results: Extraction results to validate
            sample_pris: Optional list of sample PRIs for detailed validation
            
        Returns:
            Validation report
        """
        logger.info("Starting validation process")
        
        validation_report = {
            'overall_valid': True,
            'total_count': 0,
            'valid_count': 0,
            'invalid_count': 0,
            'issues': [],
            'sample_validation': None
        }
        
        # Validate overall structure
        if not self._validate_structure(results, validation_report):
            validation_report['overall_valid'] = False
            return validation_report
        
        # Extract result list
        result_list = results.get('results', [])
        validation_report['total_count'] = len(result_list)
        
        # Validate each result
        for result in result_list:
            if self._validate_result(result):
                validation_report['valid_count'] += 1
            else:
                validation_report['invalid_count'] += 1
        
        # Perform sample validation if requested
        if sample_pris:
            validation_report['sample_validation'] = self._validate_samples(
                result_list,
                sample_pris
            )
        
        # Determine overall validity
        if validation_report['invalid_count'] > 0:
            validation_report['overall_valid'] = False
            validation_report['issues'].append(
                f"{validation_report['invalid_count']} invalid results found"
            )
        
        logger.info(
            f"Validation complete: {validation_report['valid_count']}/{validation_report['total_count']} valid"
        )
        
        return validation_report
    
    def _validate_structure(
        self,
        results: Dict[str, Any],
        report: Dict[str, Any]
    ) -> bool:
        """
        Validate the overall structure of results.
        
        Args:
            results: Results to validate
            report: Validation report to update
            
        Returns:
            True if structure is valid, False otherwise
        """
        # Check required fields
        required_fields = ['status', 'total_pris', 'results']
        for field in required_fields:
            if field not in results:
                report['issues'].append(f"Missing required field: {field}")
                logger.error(f"Results missing required field: {field}")
                return False
        
        # Check results is a list
        if not isinstance(results['results'], list):
            report['issues'].append("Results field is not a list")
            logger.error("Results field is not a list")
            return False
        
        return True
    
    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate a single result entry.
        
        Args:
            result: Result entry to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields in result
        required_fields = ['pri', 'data', 'timestamp']
        for field in required_fields:
            if field not in result:
                logger.warning(f"Result missing required field: {field}")
                return False
        
        # Validate PRI format (basic check)
        pri = result.get('pri')
        if not pri or not isinstance(pri, str):
            logger.warning(f"Invalid PRI format: {pri}")
            return False
        
        # Validate data is not empty
        data = result.get('data')
        if not data:
            logger.warning(f"Empty data for PRI: {pri}")
            return False
        
        # Validate timestamp
        timestamp = result.get('timestamp')
        if not isinstance(timestamp, (int, float)) or timestamp <= 0:
            logger.warning(f"Invalid timestamp for PRI: {pri}")
            return False
        
        return True
    
    def _validate_samples(
        self,
        results: List[Dict[str, Any]],
        sample_pris: List[str]
    ) -> Dict[str, Any]:
        """
        Perform detailed validation on sample PRIs.
        
        Args:
            results: List of all results
            sample_pris: List of sample PRIs to validate
            
        Returns:
            Sample validation report
        """
        logger.info(f"Validating {len(sample_pris)} sample PRIs")
        
        sample_report = {
            'total_samples': len(sample_pris),
            'found_samples': 0,
            'missing_samples': [],
            'sample_details': []
        }
        
        # Create a mapping of PRIs to results
        pri_to_result = {r['pri']: r for r in results if 'pri' in r}
        
        # Validate each sample
        for sample_pri in sample_pris:
            if sample_pri in pri_to_result:
                sample_report['found_samples'] += 1
                result = pri_to_result[sample_pri]
                
                # Perform detailed validation
                sample_detail = {
                    'pri': sample_pri,
                    'found': True,
                    'data_size': len(str(result.get('data', ''))),
                    'has_all_fields': all(
                        field in result
                        for field in ['pri', 'data', 'timestamp', 'bot_id']
                    )
                }
                sample_report['sample_details'].append(sample_detail)
            else:
                sample_report['missing_samples'].append(sample_pri)
                sample_report['sample_details'].append({
                    'pri': sample_pri,
                    'found': False
                })
        
        logger.info(
            f"Sample validation: {sample_report['found_samples']}/{sample_report['total_samples']} found"
        )
        
        return sample_report
    
    def check_completeness(
        self,
        expected_pris: List[str],
        actual_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if all expected PRIs are present in results.
        
        Args:
            expected_pris: List of expected PRIs
            actual_results: List of actual results
            
        Returns:
            Completeness report
        """
        actual_pris = {r['pri'] for r in actual_results if 'pri' in r}
        expected_set = set(expected_pris)
        
        missing_pris = expected_set - actual_pris
        extra_pris = actual_pris - expected_set
        
        report = {
            'expected_count': len(expected_pris),
            'actual_count': len(actual_pris),
            'missing_count': len(missing_pris),
            'extra_count': len(extra_pris),
            'missing_pris': list(missing_pris),
            'extra_pris': list(extra_pris),
            'complete': len(missing_pris) == 0
        }
        
        logger.info(
            f"Completeness check: {report['actual_count']}/{report['expected_count']} PRIs present, "
            f"{report['missing_count']} missing"
        )
        
        return report
