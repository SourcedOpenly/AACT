"""
Example usage of the Bot Manager module

This file demonstrates how to use the Bot Manager for concurrent task execution
"""

import time
import random
from bot_manager import BotManager, BotState
from bot_config import BotConfiguration, ConfigurationManager


# Example 1: Simple task processor
def simple_task_processor(task):
    """
    Simple example task processor that simulates work
    
    Args:
        task: Task to process (in this case, a number)
        
    Returns:
        Result of processing (squared number)
    """
    # Simulate some work
    time.sleep(random.uniform(0.1, 0.5))
    
    # Process the task (square the number)
    result = task * task
    
    return result


# Example 2: Task processor with potential failures
def risky_task_processor(task):
    """
    Task processor that may fail randomly
    
    Args:
        task: Task to process
        
    Returns:
        Processed result
        
    Raises:
        Exception: Random failures for demonstration
    """
    # Simulate work
    time.sleep(random.uniform(0.1, 0.3))
    
    # 20% chance of failure
    if random.random() < 0.2:
        raise Exception(f"Random failure processing task {task}")
    
    return task * 2


# Example 3: PRI (Priority) list processing
def process_pri_item(pri_item):
    """
    Process a PRI (Priority) item
    
    Args:
        pri_item: Dictionary containing PRI information
        
    Returns:
        Processed PRI item with results
    """
    # Simulate API call or database query
    time.sleep(random.uniform(0.2, 0.8))
    
    # Add processing result
    pri_item['processed'] = True
    pri_item['processing_time'] = time.time()
    pri_item['status'] = 'completed'
    
    return pri_item


def progress_callback(progress_data):
    """
    Custom callback function for progress monitoring
    
    Args:
        progress_data: List of progress dictionaries from bots
    """
    print("\n" + "="*50)
    print("PROGRESS UPDATE")
    print("="*50)
    
    for progress in progress_data:
        if progress['state'] == 'active':
            print(f"Bot {progress['bot_id']}: "
                  f"Completed: {progress['tasks_completed']}, "
                  f"Failed: {progress['tasks_failed']}")


def example_simple_execution():
    """Example: Simple execution with default configuration"""
    print("\n" + "="*60)
    print("Example 1: Simple Task Execution")
    print("="*60)
    
    # Create a list of tasks (numbers to be squared)
    tasks = list(range(1, 21))
    
    # Create bot manager with 4 bots
    manager = BotManager(
        num_bots=4,
        task_processor=simple_task_processor
    )
    
    # Execute tasks
    results = manager.execute(tasks)
    
    # Display results
    print(f"\nTotal tasks: {results['total_tasks']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {results['success_rate']:.2f}%")
    print(f"Execution time: {results['execution_time']:.2f} seconds")
    
    print("\nSample results:")
    for i, result in enumerate(results['results'][:5]):
        print(f"  Task {result.task} -> Result: {result.result} (Bot {result.bot_id})")


def example_with_configuration():
    """Example: Using configuration object"""
    print("\n" + "="*60)
    print("Example 2: Using Configuration")
    print("="*60)
    
    # Create configuration
    config = BotConfiguration(
        num_bots=3,
        max_retries=5,
        retry_delay=0.5,
        verbose=True
    )
    
    # Create tasks
    tasks = list(range(1, 16))
    
    # Create bot manager with configuration
    manager = BotManager(
        num_bots=config.num_bots,
        task_processor=risky_task_processor,
        max_retries=config.max_retries,
        retry_delay=config.retry_delay
    )
    
    # Execute tasks
    results = manager.execute(tasks)
    
    # Display results
    print(f"\nTotal tasks: {results['total_tasks']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {results['success_rate']:.2f}%")
    print(f"Execution time: {results['execution_time']:.2f} seconds")
    
    if results['failed'] > 0:
        print(f"\nFailed tasks:")
        for failed in results['failed_tasks']:
            print(f"  Task {failed['task']}: {failed['error']}")


def example_pri_list_processing():
    """Example: Processing PRI list items"""
    print("\n" + "="*60)
    print("Example 3: PRI List Processing")
    print("="*60)
    
    # Create a PRI list
    pri_list = [
        {'id': i, 'priority': random.randint(1, 5), 'data': f'Item_{i}'}
        for i in range(1, 26)
    ]
    
    print(f"Processing {len(pri_list)} PRI items...")
    
    # Create bot manager
    manager = BotManager(
        num_bots=5,
        task_processor=process_pri_item,
        max_retries=2
    )
    
    # Execute tasks
    results = manager.execute(pri_list)
    
    # Display results
    print(f"\nTotal PRI items: {results['total_tasks']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {results['success_rate']:.2f}%")
    print(f"Execution time: {results['execution_time']:.2f} seconds")
    
    # Show bot statistics
    print("\nBot Statistics:")
    for bot_progress in results['bot_progress']:
        print(f"  Bot {bot_progress['bot_id']}: "
              f"{bot_progress['tasks_completed']} completed, "
              f"{bot_progress['tasks_failed']} failed, "
              f"Time: {bot_progress['elapsed_time']:.2f}s")


def example_with_config_file():
    """Example: Loading configuration from file"""
    print("\n" + "="*60)
    print("Example 4: Using Configuration File")
    print("="*60)
    
    # Create default configuration file in temp directory
    import tempfile
    import os
    temp_dir = tempfile.gettempdir()
    config_file = os.path.join(temp_dir, 'bot_config.json')
    ConfigurationManager.create_default_config(config_file, format='json')
    print(f"Created configuration file: {config_file}")
    
    # Load configuration
    config = ConfigurationManager.load_config(filepath=config_file)
    print(f"Loaded configuration: {config.num_bots} bots, {config.max_retries} max retries")
    
    # Create tasks
    tasks = list(range(1, 11))
    
    # Create and execute
    manager = BotManager(
        num_bots=config.num_bots,
        task_processor=simple_task_processor,
        max_retries=config.max_retries,
        retry_delay=config.retry_delay
    )
    
    results = manager.execute(tasks)
    print(f"\nProcessed {results['total_tasks']} tasks in {results['execution_time']:.2f} seconds")


def example_large_scale():
    """Example: Large scale processing"""
    print("\n" + "="*60)
    print("Example 5: Large Scale Processing (1000 tasks)")
    print("="*60)
    
    # Create large task list
    tasks = list(range(1, 1001))
    
    # Create bot manager with more bots
    manager = BotManager(
        num_bots=10,
        task_processor=simple_task_processor,
        max_retries=3
    )
    
    print(f"Processing {len(tasks)} tasks with {manager.num_bots} bots...")
    
    # Execute
    results = manager.execute(tasks)
    
    # Display results
    print(f"\nTotal tasks: {results['total_tasks']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {results['success_rate']:.2f}%")
    print(f"Execution time: {results['execution_time']:.2f} seconds")
    print(f"Tasks per second: {results['total_tasks'] / results['execution_time']:.2f}")


if __name__ == '__main__':
    # Run all examples
    example_simple_execution()
    example_with_configuration()
    example_pri_list_processing()
    example_with_config_file()
    example_large_scale()
    
    print("\n" + "="*60)
    print("All examples completed successfully!")
    print("="*60)
