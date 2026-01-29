# Bot Manager Module

A Python module for managing concurrent task execution across multiple bot instances. Each bot manages its tasks independently without interfering with others, providing efficient parallel processing with built-in error handling and retry mechanisms.

## Features

- **Concurrent Execution**: Execute tasks across multiple bot instances in parallel
- **Task Distribution**: Automatically divide and assign task batches to bots
- **State Management**: Track bot states (IDLE, ACTIVE, ERROR, COMPLETED)
- **Progress Monitoring**: Real-time progress tracking across all bots
- **Error Handling**: Graceful error handling with configurable retry logic
- **Result Compilation**: Aggregate and compile results from all bots
- **Flexible Configuration**: JSON/YAML configuration support
- **Performance Optimized**: Efficient task distribution and thread management

## Installation

The module works with Python 3.7+ and has no required external dependencies for basic JSON configuration support.

For YAML configuration support, install:

```bash
pip install pyyaml
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from bot_manager import BotManager

# Define a task processor function
def process_task(task):
    # Your task processing logic here
    return task * 2

# Create a list of tasks
tasks = list(range(1, 101))

# Create bot manager with 4 concurrent bots
manager = BotManager(
    num_bots=4,
    task_processor=process_task,
    max_retries=3,
    retry_delay=1.0
)

# Execute tasks
results = manager.execute(tasks)

# Access results
print(f"Total tasks: {results['total_tasks']}")
print(f"Successful: {results['successful']}")
print(f"Failed: {results['failed']}")
print(f"Success rate: {results['success_rate']:.2f}%")
```

### Using Configuration

```python
from bot_manager import BotManager
from bot_config import BotConfiguration

# Create configuration
config = BotConfiguration(
    num_bots=5,
    max_retries=3,
    retry_delay=0.5,
    verbose=True
)

# Create bot manager
manager = BotManager(
    num_bots=config.num_bots,
    task_processor=process_task,
    max_retries=config.max_retries,
    retry_delay=config.retry_delay
)

# Execute tasks
results = manager.execute(tasks)
```

### Loading Configuration from File

```python
from bot_config import ConfigurationManager

# Create default configuration file
ConfigurationManager.create_default_config('config.json', format='json')

# Load configuration
config = ConfigurationManager.load_config(filepath='config.json')

# Use configuration with bot manager
manager = BotManager(
    num_bots=config.num_bots,
    task_processor=process_task,
    max_retries=config.max_retries,
    retry_delay=config.retry_delay
)
```

## Architecture

### Components

#### BotManager
Main orchestrator that manages multiple bot instances and coordinates task execution.

**Key Methods:**
- `execute(tasks)`: Execute tasks across all bots
- `get_progress()`: Get current progress of all bots
- `monitor_progress()`: Real-time progress monitoring

#### Bot
Individual bot instance that processes tasks independently.

**Key Features:**
- Independent task processing
- Retry logic for failed tasks
- Progress tracking
- Thread-safe state management

#### BotConfiguration
Configuration management for bot parameters.

**Configurable Parameters:**
- `num_bots`: Number of concurrent bots (default: 4)
- `max_retries`: Maximum retry attempts (default: 3)
- `retry_delay`: Delay between retries in seconds (default: 1.0)
- `verbose`: Enable detailed logging (default: False)
- `monitor_interval`: Progress monitoring interval (default: 1.0)

### State Management

Bots can be in one of four states:
- **IDLE**: Bot is initialized but not yet processing
- **ACTIVE**: Bot is currently processing tasks
- **ERROR**: Bot encountered an error
- **COMPLETED**: Bot finished all assigned tasks

## Advanced Usage

### Custom Task Processor

```python
def custom_processor(task):
    """
    Custom task processor with API calls, database operations, etc.
    """
    # Your custom logic
    result = perform_complex_operation(task)
    return result

manager = BotManager(
    num_bots=8,
    task_processor=custom_processor,
    max_retries=5
)
```

### Progress Monitoring with Callback

```python
def progress_callback(progress_data):
    """Custom progress reporting"""
    for progress in progress_data:
        if progress['state'] == 'active':
            print(f"Bot {progress['bot_id']}: {progress['tasks_completed']} completed")

# Start monitoring in a separate thread
import threading
monitor_thread = threading.Thread(
    target=manager.monitor_progress,
    args=(1.0, progress_callback)
)
monitor_thread.start()
```

### PRI List Processing

```python
# Create PRI list
pri_list = [
    {'id': i, 'priority': priority, 'data': data}
    for i in range(1, 1001)
]

# Process PRI items
def process_pri_item(item):
    # Process the PRI item
    item['processed'] = True
    item['status'] = 'completed'
    return item

# Execute with bot manager
manager = BotManager(num_bots=10, task_processor=process_pri_item)
results = manager.execute(pri_list)
```

## Result Structure

The `execute()` method returns a dictionary with the following structure:

```python
{
    'total_tasks': 100,           # Total number of tasks
    'successful': 95,              # Successfully completed tasks
    'failed': 5,                   # Failed tasks
    'success_rate': 95.0,          # Success percentage
    'execution_time': 12.5,        # Total execution time in seconds
    'results': [TaskResult, ...],  # List of TaskResult objects
    'bot_progress': [...],         # Progress data for each bot
    'failed_tasks': [...]          # Details of failed tasks
}
```

### TaskResult Object

```python
TaskResult(
    bot_id=0,                     # ID of bot that processed the task
    task=task_data,               # Original task data
    success=True,                 # Whether task succeeded
    result=processed_data,        # Result of processing (if successful)
    error=None,                   # Error message (if failed)
    execution_time=0.5            # Time taken to process
)
```

## Performance Optimization

The module includes several optimizations:

1. **Efficient Task Distribution**: Tasks are divided evenly across bots with optimal batch sizing
2. **Thread Pool Execution**: Uses `ThreadPoolExecutor` for efficient concurrent execution
3. **Minimal Lock Contention**: Thread-safe operations with minimal locking
4. **Lazy Result Compilation**: Results are collected as they complete

### Performance Tips

- Adjust `num_bots` based on task characteristics (CPU-bound vs I/O-bound)
- For CPU-bound tasks: `num_bots = CPU_count`
- For I/O-bound tasks: `num_bots = CPU_count * 2-4`
- Use appropriate `retry_delay` to avoid overwhelming external services
- Monitor progress at reasonable intervals (avoid excessive polling)

## Error Handling

The module provides comprehensive error handling:

- **Automatic Retries**: Failed tasks are automatically retried up to `max_retries`
- **Graceful Degradation**: Individual task failures don't stop other tasks
- **Error Tracking**: All errors are logged and included in results
- **Exception Safety**: Thread-safe error handling

Example with error handling:

```python
def task_with_potential_errors(task):
    if task % 10 == 0:
        raise Exception("Simulated error")
    return task * 2

manager = BotManager(
    num_bots=4,
    task_processor=task_with_potential_errors,
    max_retries=3,
    retry_delay=0.5
)

results = manager.execute(tasks)

# Check for failures
if results['failed'] > 0:
    print(f"Failed tasks: {results['failed']}")
    for failed in results['failed_tasks']:
        print(f"Task {failed['task']}: {failed['error']}")
```

## Examples

See `examples.py` for complete working examples including:

1. Simple task execution
2. Configuration usage
3. PRI list processing
4. Configuration file usage
5. Large-scale processing (1000+ tasks)

Run examples:
```bash
python examples.py
```

## Configuration File Format

### JSON Format

```json
{
  "num_bots": 4,
  "max_retries": 3,
  "retry_delay": 1.0,
  "verbose": false,
  "monitor_interval": 1.0,
  "task_processor_config": {}
}
```

### YAML Format

```yaml
num_bots: 4
max_retries: 3
retry_delay: 1.0
verbose: false
monitor_interval: 1.0
task_processor_config: {}
```

## API Reference

### BotManager

#### `__init__(num_bots, task_processor, max_retries=3, retry_delay=1.0)`
Initialize the bot manager.

**Parameters:**
- `num_bots` (int): Number of concurrent bots
- `task_processor` (Callable): Function to process individual tasks
- `max_retries` (int): Maximum retry attempts for failed tasks
- `retry_delay` (float): Delay in seconds between retries

#### `execute(tasks) -> Dict[str, Any]`
Execute tasks across all bots concurrently.

**Parameters:**
- `tasks` (List[Any]): List of tasks to process

**Returns:**
- Dictionary containing execution results and statistics

#### `get_progress() -> List[Dict[str, Any]]`
Get current progress of all bots.

**Returns:**
- List of progress dictionaries for each bot

#### `monitor_progress(interval=1.0, callback=None)`
Monitor progress in real-time.

**Parameters:**
- `interval` (float): Time between progress checks
- `callback` (Callable): Optional callback function

### Bot

#### `__init__(bot_id, task_processor, max_retries=3, retry_delay=1.0)`
Initialize a bot instance.

#### `process_tasks(tasks) -> List[TaskResult]`
Process a list of assigned tasks.

#### `get_progress() -> BotProgress`
Get current progress of the bot.

### BotConfiguration

See configuration section for available parameters and defaults.

## Testing

Run the examples to test functionality:

```bash
python examples.py
```

## License

This module is provided as-is for the AACT project.

## Contributing

For issues or improvements, please submit a pull request or issue to the AACT repository.
