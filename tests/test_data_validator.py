"""
Tests for Data Validator Module
"""

import pytest
from data_validator import DataValidator


class TestDataValidator:
    """Test suite for DataValidator class."""
    
    def test_initialization(self):
        """Test DataValidator initialization."""
        validator = DataValidator()
        assert validator is not None
    
    def test_validate_valid_results(self):
        """Test validation of valid results."""
        validator = DataValidator()
        
        results = {
            'status': 'completed',
            'total_pris': 2,
            'results': [
                {'pri': 'PRI001', 'data': {'field': 'value1'}, 'timestamp': 123456.0},
                {'pri': 'PRI002', 'data': {'field': 'value2'}, 'timestamp': 123457.0}
            ]
        }
        
        report = validator.validate(results)
        
        assert report['overall_valid'] is True
        assert report['total_count'] == 2
        assert report['valid_count'] == 2
        assert report['invalid_count'] == 0
    
    def test_validate_missing_required_field(self):
        """Test validation with missing required field."""
        validator = DataValidator()
        
        results = {
            'total_pris': 1,
            'results': []
        }
        
        report = validator.validate(results)
        
        assert report['overall_valid'] is False
        assert len(report['issues']) > 0
    
    def test_validate_result_missing_fields(self):
        """Test validation of results with missing fields."""
        validator = DataValidator()
        
        results = {
            'status': 'completed',
            'total_pris': 2,
            'results': [
                {'pri': 'PRI001', 'data': {'field': 'value1'}, 'timestamp': 123456.0},
                {'pri': 'PRI002', 'timestamp': 123457.0}  # Missing 'data' field
            ]
        }
        
        report = validator.validate(results)
        
        assert report['overall_valid'] is False
        assert report['total_count'] == 2
        assert report['valid_count'] == 1
        assert report['invalid_count'] == 1
    
    def test_validate_with_samples(self):
        """Test validation with sample PRIs."""
        validator = DataValidator()
        
        results = {
            'status': 'completed',
            'total_pris': 3,
            'results': [
                {'pri': 'PRI001', 'data': {'field': 'value1'}, 'timestamp': 123456.0, 'bot_id': 0},
                {'pri': 'PRI002', 'data': {'field': 'value2'}, 'timestamp': 123457.0, 'bot_id': 0},
                {'pri': 'PRI003', 'data': {'field': 'value3'}, 'timestamp': 123458.0, 'bot_id': 1}
            ]
        }
        
        sample_pris = ['PRI001', 'PRI003']
        report = validator.validate(results, sample_pris=sample_pris)
        
        assert report['sample_validation'] is not None
        assert report['sample_validation']['total_samples'] == 2
        assert report['sample_validation']['found_samples'] == 2
        assert len(report['sample_validation']['missing_samples']) == 0
    
    def test_validate_with_missing_samples(self):
        """Test validation with missing sample PRIs."""
        validator = DataValidator()
        
        results = {
            'status': 'completed',
            'total_pris': 2,
            'results': [
                {'pri': 'PRI001', 'data': {'field': 'value1'}, 'timestamp': 123456.0},
                {'pri': 'PRI002', 'data': {'field': 'value2'}, 'timestamp': 123457.0}
            ]
        }
        
        sample_pris = ['PRI001', 'PRI999']  # PRI999 is missing
        report = validator.validate(results, sample_pris=sample_pris)
        
        assert report['sample_validation']['found_samples'] == 1
        assert 'PRI999' in report['sample_validation']['missing_samples']
    
    def test_check_completeness_all_present(self):
        """Test completeness check with all PRIs present."""
        validator = DataValidator()
        
        expected_pris = ['PRI001', 'PRI002', 'PRI003']
        actual_results = [
            {'pri': 'PRI001', 'data': {}},
            {'pri': 'PRI002', 'data': {}},
            {'pri': 'PRI003', 'data': {}}
        ]
        
        report = validator.check_completeness(expected_pris, actual_results)
        
        assert report['complete'] is True
        assert report['expected_count'] == 3
        assert report['actual_count'] == 3
        assert report['missing_count'] == 0
    
    def test_check_completeness_missing_pris(self):
        """Test completeness check with missing PRIs."""
        validator = DataValidator()
        
        expected_pris = ['PRI001', 'PRI002', 'PRI003']
        actual_results = [
            {'pri': 'PRI001', 'data': {}},
            {'pri': 'PRI003', 'data': {}}
        ]
        
        report = validator.check_completeness(expected_pris, actual_results)
        
        assert report['complete'] is False
        assert report['missing_count'] == 1
        assert 'PRI002' in report['missing_pris']
    
    def test_check_completeness_extra_pris(self):
        """Test completeness check with extra PRIs."""
        validator = DataValidator()
        
        expected_pris = ['PRI001', 'PRI002']
        actual_results = [
            {'pri': 'PRI001', 'data': {}},
            {'pri': 'PRI002', 'data': {}},
            {'pri': 'PRI999', 'data': {}}
        ]
        
        report = validator.check_completeness(expected_pris, actual_results)
        
        assert report['extra_count'] == 1
        assert 'PRI999' in report['extra_pris']
