"""
AACT Bot Manager Module

A comprehensive module for managing concurrent task execution across multiple bot instances.
"""

__version__ = '1.0.0'
__author__ = 'AACT Project'

from bot_manager import (
    BotManager,
    Bot,
    BotState,
    BotProgress,
    TaskResult
)

from bot_config import (
    BotConfiguration,
    ConfigurationManager
)

__all__ = [
    'BotManager',
    'Bot',
    'BotState',
    'BotProgress',
    'TaskResult',
    'BotConfiguration',
    'ConfigurationManager',
]
