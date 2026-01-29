# Quick Start Guide - Bot Manager Module

This guide will help you get started with the Bot Manager module in under 5 minutes.

## Installation

1. Clone the repository or download the files
2. No dependencies required for basic usage (JSON configuration only)
3. Optional: Install PyYAML for YAML configuration support
   ```bash
   pip install pyyaml
   ```

## 5-Minute Tutorial

### Step 1: Import the Module

```python
from bot_manager import BotManager
```

### Step 2: Define Your Task Processor

This is a function that processes a single task:

```python
def my_task_processor(task):
    # Your custom logic here
    # For example, multiply by 2
    result = task * 2
    return result
```

### Step 3: Create Tasks

```python
# Create a list of tasks to process
tasks = list(range(1, 101))  # Process numbers 1 to 100
```

### Step 4: Create and Configure Bot Manager

```python
# Create a bot manager with 4 concurrent bots
manager = BotManager(
    num_bots=4,              # Number of concurrent bots
    task_processor=my_task_processor,  # Your task processing function
    max_retries=3,           # Retry failed tasks up to 3 times
    retry_delay=1.0          # Wait 1 second between retries
)
```

### Step 5: Execute Tasks

```python
# Execute all tasks across the bots
results = manager.execute(tasks)
```

### Step 6: Review Results

```python
# Print summary
print(f"Total tasks: {results['total_tasks']}")
print(f"Successful: {results['successful']}")
print(f"Failed: {results['failed']}")
print(f"Success rate: {results['success_rate']:.2f}%")
print(f"Execution time: {results['execution_time']:.2f} seconds")

# Access individual results
for result in results['results'][:5]:  # Show first 5
    print(f"Task {result.task} -> Result: {result.result}")
```

## Complete Working Example

```python
from bot_manager import BotManager
import time

# Step 1: Define task processor
def process_number(num):
    # Simulate some work
    time.sleep(0.1)
    return num ** 2

# Step 2: Create tasks
tasks = list(range(1, 21))

# Step 3: Create bot manager
manager = BotManager(
    num_bots=4,
    task_processor=process_number,
    max_retries=2
)

# Step 4: Execute
results = manager.execute(tasks)

# Step 5: Display results
print(f"\nProcessed {results['total_tasks']} tasks")
print(f"Success rate: {results['success_rate']:.1f}%")
print(f"Time taken: {results['execution_time']:.2f} seconds")
```

## Real-World Example: Processing API Requests

```python
import requests
from bot_manager import BotManager

def fetch_user_data(user_id):
    """Fetch user data from an API"""
    response = requests.get(f'https://api.example.com/users/{user_id}')
    response.raise_for_status()
    return response.json()

# Process 100 user IDs
user_ids = list(range(1, 101))

# Use 10 concurrent bots for API requests
manager = BotManager(
    num_bots=10,
    task_processor=fetch_user_data,
    max_retries=3,
    retry_delay=2.0  # Wait 2 seconds between retries for API rate limits
)

results = manager.execute(user_ids)

# Check for failures
if results['failed'] > 0:
    print(f"Failed to fetch {results['failed']} users")
    for failed in results['failed_tasks']:
        print(f"User {failed['task']}: {failed['error']}")
```

## Using Configuration Files

### Create a configuration file:

```python
from bot_config import ConfigurationManager

# Create default config
ConfigurationManager.create_default_config('my_config.json', format='json')
```

### Load and use configuration:

```python
from bot_config import ConfigurationManager
from bot_manager import BotManager

# Load configuration
config = ConfigurationManager.load_config(filepath='my_config.json')

# Create bot manager with config
manager = BotManager(
    num_bots=config.num_bots,
    task_processor=my_task_processor,
    max_retries=config.max_retries,
    retry_delay=config.retry_delay
)
```

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_bots` | 4 | Number of concurrent bots |
| `max_retries` | 3 | Maximum retry attempts for failed tasks |
| `retry_delay` | 1.0 | Delay in seconds between retries |
| `verbose` | False | Enable detailed logging |
| `monitor_interval` | 1.0 | Progress monitoring interval in seconds |

## Tips for Best Performance

1. **CPU-bound tasks**: Set `num_bots` equal to CPU count
2. **I/O-bound tasks** (API calls, file I/O): Set `num_bots` to 2-4x CPU count
3. **API rate limits**: Use appropriate `retry_delay` to avoid overwhelming APIs
4. **Large task lists**: Consider processing in batches if memory is a concern

## Common Patterns

### Pattern 1: Database Queries

```python
def query_database(query_id):
    conn = get_db_connection()
    result = conn.execute(f"SELECT * FROM table WHERE id = {query_id}")
    return result.fetchall()

manager = BotManager(num_bots=5, task_processor=query_database)
```

### Pattern 2: File Processing

```python
def process_file(filepath):
    with open(filepath, 'r') as f:
        data = f.read()
    # Process data
    return processed_data

file_list = ['file1.txt', 'file2.txt', 'file3.txt']
manager = BotManager(num_bots=3, task_processor=process_file)
```

### Pattern 3: Web Scraping

```python
from bs4 import BeautifulSoup
import requests

def scrape_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup.find_all('div', class_='content')

urls = ['http://example.com/page1', 'http://example.com/page2']
manager = BotManager(num_bots=5, task_processor=scrape_page, max_retries=3)
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Run `python examples.py` to see more examples
- Check `test_bot_manager.py` for usage patterns
- Customize the configuration for your use case

## Troubleshooting

### ImportError: No module named 'yaml'
- YAML support is optional. Either install PyYAML or use JSON configuration

### Tasks taking too long
- Reduce `num_bots` if you're overwhelming external services
- Check your `task_processor` function for bottlenecks
- Consider adding timeout logic to your task processor

### High memory usage
- Process tasks in smaller batches
- Make sure your task processor doesn't accumulate large data structures

## Getting Help

- Review the comprehensive API documentation in [README.md](README.md)
- Check the examples in `examples.py`
- Review test cases in `test_bot_manager.py` for usage patterns
