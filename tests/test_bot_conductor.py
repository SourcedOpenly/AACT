"""
Tests for Bot Conductor Module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bot_conductor import BotConductor


class TestBotConductor:
    """Test suite for BotConductor class."""
    
    def test_initialization(self):
        """Test BotConductor initialization."""
        conductor = BotConductor(max_workers=5, batch_size=30)
        
        assert conductor.max_workers == 5
        assert conductor.batch_size == 30
        assert conductor.validator is not None
        assert conductor.results_lock is not None
    
    def test_divide_pris_empty_list(self):
        """Test dividing an empty PRI list."""
        conductor = BotConductor()
        batches = conductor.divide_pris([])
        
        assert batches == []
    
    def test_divide_pris_single_batch(self):
        """Test dividing PRIs into a single batch."""
        conductor = BotConductor(batch_size=30)
        pris = [f"PRI{i:03d}" for i in range(20)]
        batches = conductor.divide_pris(pris)
        
        assert len(batches) == 1
        assert len(batches[0]) == 20
        assert batches[0] == pris
    
    def test_divide_pris_multiple_batches(self):
        """Test dividing PRIs into multiple batches."""
        conductor = BotConductor(batch_size=30)
        pris = [f"PRI{i:03d}" for i in range(75)]
        batches = conductor.divide_pris(pris)
        
        assert len(batches) == 3
        assert len(batches[0]) == 30
        assert len(batches[1]) == 30
        assert len(batches[2]) == 15
    
    def test_divide_pris_exact_batch_size(self):
        """Test dividing PRIs with exact batch size."""
        conductor = BotConductor(batch_size=30)
        pris = [f"PRI{i:03d}" for i in range(60)]
        batches = conductor.divide_pris(pris)
        
        assert len(batches) == 2
        assert len(batches[0]) == 30
        assert len(batches[1]) == 30
    
    @patch('bot_conductor.PhoenixBot')
    def test_process_batch_success(self, mock_bot_class):
        """Test successful batch processing."""
        conductor = BotConductor()
        
        # Mock bot instance
        mock_bot = MagicMock()
        mock_bot.authenticate.return_value = True
        mock_bot.extract_batch_data.return_value = {
            'results': [
                {'pri': 'PRI001', 'data': {'test': 'data1'}, 'timestamp': 123456},
                {'pri': 'PRI002', 'data': {'test': 'data2'}, 'timestamp': 123457}
            ],
            'failed': []
        }
        mock_bot_class.return_value = mock_bot
        
        batch = ['PRI001', 'PRI002']
        credentials = {'base_url': 'http://test.com', 'username': 'test', 'password': 'pass'}
        
        result = conductor._process_batch(batch, 0, credentials)
        
        assert len(result['results']) == 2
        assert len(result['failed']) == 0
        mock_bot.authenticate.assert_called_once()
        mock_bot.extract_batch_data.assert_called_once_with(batch, None)
        mock_bot.cleanup.assert_called_once()
    
    @patch('bot_conductor.PhoenixBot')
    def test_process_batch_auth_failure(self, mock_bot_class):
        """Test batch processing with authentication failure."""
        conductor = BotConductor()
        
        # Mock bot instance with failed auth
        mock_bot = MagicMock()
        mock_bot.authenticate.return_value = False
        mock_bot_class.return_value = mock_bot
        
        batch = ['PRI001', 'PRI002']
        credentials = {'base_url': 'http://test.com', 'username': 'test', 'password': 'pass'}
        
        result = conductor._process_batch(batch, 0, credentials)
        
        assert len(result['results']) == 0
        assert result['failed'] == batch
        mock_bot.authenticate.assert_called_once()
        mock_bot.cleanup.assert_called_once()
    
    def test_get_statistics(self):
        """Test statistics generation."""
        conductor = BotConductor()
        
        results = {
            'total_pris': 100,
            'successful': 95,
            'failed': 5
        }
        
        stats = conductor.get_statistics(results)
        
        assert stats['total_pris_processed'] == 100
        assert stats['successful_extractions'] == 95
        assert stats['failed_extractions'] == 5
        assert stats['success_rate'] == 95.0
    
    def test_get_statistics_zero_pris(self):
        """Test statistics with zero PRIs."""
        conductor = BotConductor()
        
        results = {
            'total_pris': 0,
            'successful': 0,
            'failed': 0
        }
        
        stats = conductor.get_statistics(results)
        
        assert stats['success_rate'] == 0.0
    
    @patch('bot_conductor.PhoenixBot')
    def test_extract_data_empty_list(self, mock_bot_class):
        """Test data extraction with empty PRI list."""
        conductor = BotConductor()
        
        credentials = {'base_url': 'http://test.com', 'username': 'test', 'password': 'pass'}
        result = conductor.extract_data([], credentials)
        
        assert result['status'] == 'error'
        assert result['message'] == 'No PRIs to process'
        assert result['results'] == []
