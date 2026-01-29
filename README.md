# AACT - Bot Conductor Module

A Python module for managing concurrent data extraction tasks from Phoenix.

## Overview

The Bot Conductor Module is designed to efficiently manage multiple bot instances that extract data from Phoenix concurrently. It automatically divides the workload, manages authentication, oversees data extraction, and validates results.

## Key Features

1. **Automatic PRI Division**: Splits PRI lists into batches of up to 30 PRIs per bot
2. **Concurrent Bot Management**: Initiates and oversees multiple bot instances
3. **Secure Authentication**: Ensures each bot obtains a unique cookie
4. **Data Extraction Oversight**: Monitors bots during Phoenix query execution
5. **Concurrency Handling**: Uses threading for smooth concurrent operations
6. **Result Validation**: Validates extracted data for sample PRIs

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from bot_conductor import BotConductor

# Initialize the conductor
conductor = BotConductor(
    max_workers=5,
    batch_size=30
)

# Run data extraction
results = conductor.extract_data(
    pri_list=['PRI001', 'PRI002', 'PRI003', ...],
    phoenix_credentials={
        'base_url': 'https://phoenix.example.com',
        'username': 'user',
        'password': 'pass'
    }
)

# Validate results
validation_report = conductor.validate_results(results, sample_pris=['PRI001'])
```

## Architecture

- `bot_conductor.py`: Main orchestrator for managing concurrent bots
- `phoenix_bot.py`: Individual bot implementation for data extraction
- `auth_manager.py`: Authentication and session management
- `data_validator.py`: Result validation and verification

## Testing

```bash
pytest tests/ -v --cov=.
```

## License

MIT License
