"""
Unit tests for Bot Manager module
"""

import unittest
import time
import threading
from bot_manager import BotManager, Bot, BotState, BotProgress, TaskResult
from bot_config import BotConfiguration, ConfigurationManager
import tempfile
import os


class TestBotProgress(unittest.TestCase):
    """Test BotProgress class"""
    
    def test_initialization(self):
        """Test BotProgress initialization"""
        progress = BotProgress(bot_id=1)
        self.assertEqual(progress.bot_id, 1)
        self.assertEqual(progress.state, BotState.IDLE)
        self.assertEqual(progress.tasks_completed, 0)
        self.assertEqual(progress.tasks_failed, 0)
    
    def test_elapsed_time(self):
        """Test elapsed time calculation"""
        progress = BotProgress(bot_id=1)
        progress.start_time = time.time()
        time.sleep(0.1)
        elapsed = progress.get_elapsed_time()
        self.assertGreater(elapsed, 0.1)
        self.assertLess(elapsed, 0.2)
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        progress = BotProgress(bot_id=1, state=BotState.ACTIVE)
        progress.tasks_completed = 5
        d = progress.to_dict()
        self.assertEqual(d['bot_id'], 1)
        self.assertEqual(d['state'], 'active')
        self.assertEqual(d['tasks_completed'], 5)


class TestTaskResult(unittest.TestCase):
    """Test TaskResult class"""
    
    def test_successful_result(self):
        """Test successful task result"""
        result = TaskResult(
            bot_id=1,
            task="test_task",
            success=True,
            result="processed",
            execution_time=0.5
        )
        self.assertTrue(result.success)
        self.assertEqual(result.result, "processed")
        self.assertIsNone(result.error)
    
    def test_failed_result(self):
        """Test failed task result"""
        result = TaskResult(
            bot_id=1,
            task="test_task",
            success=False,
            error="Test error",
            execution_time=0.5
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Test error")
        self.assertIsNone(result.result)


class TestBot(unittest.TestCase):
    """Test Bot class"""
    
    def simple_processor(self, task):
        """Simple task processor for testing"""
        return task * 2
    
    def failing_processor(self, task):
        """Task processor that always fails"""
        raise Exception("Test failure")
    
    def test_bot_initialization(self):
        """Test bot initialization"""
        bot = Bot(bot_id=1, task_processor=self.simple_processor)
        self.assertEqual(bot.bot_id, 1)
        self.assertEqual(bot.max_retries, 3)
        self.assertEqual(bot.progress.state, BotState.IDLE)
    
    def test_process_single_task_success(self):
        """Test successful single task processing"""
        bot = Bot(bot_id=1, task_processor=self.simple_processor)
        tasks = [5]
        results = bot.process_tasks(tasks)
        
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].success)
        self.assertEqual(results[0].result, 10)
        self.assertEqual(bot.progress.tasks_completed, 1)
        self.assertEqual(bot.progress.tasks_failed, 0)
    
    def test_process_multiple_tasks(self):
        """Test multiple task processing"""
        bot = Bot(bot_id=1, task_processor=self.simple_processor)
        tasks = [1, 2, 3, 4, 5]
        results = bot.process_tasks(tasks)
        
        self.assertEqual(len(results), 5)
        self.assertTrue(all(r.success for r in results))
        self.assertEqual([r.result for r in results], [2, 4, 6, 8, 10])
        self.assertEqual(bot.progress.tasks_completed, 5)
    
    def test_process_task_with_retry(self):
        """Test task processing with retries"""
        bot = Bot(
            bot_id=1,
            task_processor=self.failing_processor,
            max_retries=3,
            retry_delay=0.1
        )
        tasks = [1]
        start_time = time.time()
        results = bot.process_tasks(tasks)
        elapsed = time.time() - start_time
        
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)
        self.assertIsNotNone(results[0].error)
        self.assertEqual(bot.progress.tasks_failed, 1)
        # 3 attempts total with 2 delays of 0.1s between them = 0.2s minimum
        self.assertGreater(elapsed, 0.19)
    
    def test_bot_state_transitions(self):
        """Test bot state transitions"""
        bot = Bot(bot_id=1, task_processor=self.simple_processor)
        self.assertEqual(bot.progress.state, BotState.IDLE)
        
        tasks = [1, 2, 3]
        bot.process_tasks(tasks)
        
        self.assertEqual(bot.progress.state, BotState.COMPLETED)
    
    def test_get_progress(self):
        """Test getting bot progress"""
        bot = Bot(bot_id=1, task_processor=self.simple_processor)
        progress = bot.get_progress()
        
        self.assertIsInstance(progress, BotProgress)
        self.assertEqual(progress.bot_id, 1)


class TestBotManager(unittest.TestCase):
    """Test BotManager class"""
    
    def simple_processor(self, task):
        """Simple task processor for testing"""
        time.sleep(0.01)  # Simulate work
        return task * 2
    
    def test_manager_initialization(self):
        """Test bot manager initialization"""
        manager = BotManager(
            num_bots=4,
            task_processor=self.simple_processor
        )
        self.assertEqual(manager.num_bots, 4)
        self.assertEqual(len(manager.bots), 0)  # Not created until execute
    
    def test_invalid_num_bots(self):
        """Test initialization with invalid number of bots"""
        with self.assertRaises(ValueError):
            BotManager(num_bots=0, task_processor=self.simple_processor)
        
        with self.assertRaises(ValueError):
            BotManager(num_bots=-1, task_processor=self.simple_processor)
    
    def test_task_division(self):
        """Test task division among bots"""
        manager = BotManager(num_bots=4, task_processor=self.simple_processor)
        tasks = list(range(10))
        batches = manager._divide_tasks(tasks)
        
        self.assertEqual(len(batches), 4)
        # Check all tasks are distributed
        all_tasks = []
        for batch in batches:
            all_tasks.extend(batch)
        self.assertEqual(sorted(all_tasks), sorted(tasks))
    
    def test_even_task_division(self):
        """Test even task division"""
        manager = BotManager(num_bots=4, task_processor=self.simple_processor)
        tasks = list(range(20))  # Divides evenly by 4
        batches = manager._divide_tasks(tasks)
        
        # All batches should have 5 tasks
        self.assertTrue(all(len(batch) == 5 for batch in batches))
    
    def test_uneven_task_division(self):
        """Test uneven task division"""
        manager = BotManager(num_bots=4, task_processor=self.simple_processor)
        tasks = list(range(10))  # 10 doesn't divide evenly by 4
        batches = manager._divide_tasks(tasks)
        
        # First 2 bots should get 3 tasks, last 2 should get 2
        self.assertEqual(len(batches[0]), 3)
        self.assertEqual(len(batches[1]), 3)
        self.assertEqual(len(batches[2]), 2)
        self.assertEqual(len(batches[3]), 2)
    
    def test_execute_empty_tasks(self):
        """Test execution with empty task list"""
        manager = BotManager(num_bots=4, task_processor=self.simple_processor)
        results = manager.execute([])
        
        self.assertEqual(results['total_tasks'], 0)
        self.assertEqual(results['successful'], 0)
        self.assertEqual(results['failed'], 0)
    
    def test_execute_simple_tasks(self):
        """Test simple task execution"""
        manager = BotManager(num_bots=4, task_processor=self.simple_processor)
        tasks = list(range(1, 21))
        results = manager.execute(tasks)
        
        self.assertEqual(results['total_tasks'], 20)
        self.assertEqual(results['successful'], 20)
        self.assertEqual(results['failed'], 0)
        self.assertEqual(results['success_rate'], 100.0)
        self.assertGreater(results['execution_time'], 0)
    
    def test_execute_with_failures(self):
        """Test execution with some failures"""
        def sometimes_failing_processor(task):
            if task % 5 == 0:
                raise Exception("Divisible by 5")
            return task * 2
        
        manager = BotManager(
            num_bots=2,
            task_processor=sometimes_failing_processor,
            max_retries=1,
            retry_delay=0.01
        )
        tasks = list(range(1, 11))
        results = manager.execute(tasks)
        
        self.assertEqual(results['total_tasks'], 10)
        self.assertGreater(results['failed'], 0)
        self.assertLess(results['success_rate'], 100.0)
    
    def test_concurrent_execution(self):
        """Test that bots execute concurrently"""
        def slow_processor(task):
            time.sleep(0.1)
            return task
        
        manager = BotManager(num_bots=4, task_processor=slow_processor)
        tasks = list(range(20))
        
        start_time = time.time()
        results = manager.execute(tasks)
        elapsed = time.time() - start_time
        
        # If sequential, would take 20 * 0.1 = 2 seconds
        # With 4 bots, should take around 0.5 seconds (5 tasks per bot)
        self.assertLess(elapsed, 1.5)  # Should be much less than sequential
        self.assertEqual(results['successful'], 20)
    
    def test_get_progress(self):
        """Test getting progress from manager"""
        manager = BotManager(num_bots=4, task_processor=self.simple_processor)
        tasks = list(range(10))
        manager.execute(tasks)
        
        progress = manager.get_progress()
        self.assertEqual(len(progress), 4)
        self.assertTrue(all(isinstance(p, dict) for p in progress))
    
    def test_result_compilation(self):
        """Test result compilation"""
        manager = BotManager(num_bots=2, task_processor=self.simple_processor)
        tasks = list(range(10))
        results = manager.execute(tasks)
        
        self.assertIn('total_tasks', results)
        self.assertIn('successful', results)
        self.assertIn('failed', results)
        self.assertIn('success_rate', results)
        self.assertIn('execution_time', results)
        self.assertIn('results', results)
        self.assertIn('bot_progress', results)
        self.assertIn('failed_tasks', results)


class TestBotConfiguration(unittest.TestCase):
    """Test BotConfiguration class"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = BotConfiguration()
        self.assertEqual(config.num_bots, 4)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.retry_delay, 1.0)
        self.assertFalse(config.verbose)
    
    def test_custom_configuration(self):
        """Test custom configuration"""
        config = BotConfiguration(
            num_bots=8,
            max_retries=5,
            retry_delay=0.5,
            verbose=True
        )
        self.assertEqual(config.num_bots, 8)
        self.assertEqual(config.max_retries, 5)
        self.assertEqual(config.retry_delay, 0.5)
        self.assertTrue(config.verbose)
    
    def test_invalid_configuration(self):
        """Test validation of invalid configuration"""
        with self.assertRaises(ValueError):
            BotConfiguration(num_bots=0)
        
        with self.assertRaises(ValueError):
            BotConfiguration(max_retries=-1)
        
        with self.assertRaises(ValueError):
            BotConfiguration(retry_delay=-1.0)
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        config = BotConfiguration(num_bots=5)
        d = config.to_dict()
        self.assertEqual(d['num_bots'], 5)
        self.assertIsInstance(d, dict)
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        config_dict = {
            'num_bots': 6,
            'max_retries': 4,
            'verbose': True
        }
        config = BotConfiguration.from_dict(config_dict)
        self.assertEqual(config.num_bots, 6)
        self.assertEqual(config.max_retries, 4)
        self.assertTrue(config.verbose)
    
    def test_json_file_operations(self):
        """Test JSON file save and load"""
        config = BotConfiguration(num_bots=7, max_retries=2)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            config.save_json(filepath)
            loaded_config = BotConfiguration.from_json_file(filepath)
            
            self.assertEqual(loaded_config.num_bots, 7)
            self.assertEqual(loaded_config.max_retries, 2)
        finally:
            os.unlink(filepath)


class TestConfigurationManager(unittest.TestCase):
    """Test ConfigurationManager class"""
    
    def test_load_default_config(self):
        """Test loading default configuration"""
        config = ConfigurationManager.load_config()
        self.assertIsInstance(config, BotConfiguration)
        self.assertEqual(config.num_bots, 4)
    
    def test_load_from_dict(self):
        """Test loading from dictionary"""
        config_dict = {'num_bots': 5, 'max_retries': 2}
        config = ConfigurationManager.load_config(config_dict=config_dict)
        self.assertEqual(config.num_bots, 5)
        self.assertEqual(config.max_retries, 2)
    
    def test_create_default_config_json(self):
        """Test creating default JSON config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            ConfigurationManager.create_default_config(filepath, format='json')
            self.assertTrue(os.path.exists(filepath))
            
            config = ConfigurationManager.load_config(filepath=filepath)
            self.assertEqual(config.num_bots, 4)
        finally:
            os.unlink(filepath)
    
    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file"""
        with self.assertRaises(FileNotFoundError):
            ConfigurationManager.load_config(filepath='nonexistent.json')
    
    def test_unsupported_format(self):
        """Test unsupported file format"""
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            filepath = f.name
            f.write("test")
        
        try:
            with self.assertRaises(ValueError):
                ConfigurationManager.load_config(filepath=filepath)
        finally:
            os.unlink(filepath)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
