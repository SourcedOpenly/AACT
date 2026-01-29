"""
Configuration module for Bot Manager

Handles configuration loading, validation, and management
"""

import json
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class BotConfiguration:
    """Configuration settings for the Bot Manager"""
    
    # Number of concurrent bots
    num_bots: int = 4
    
    # Maximum retry attempts for failed tasks
    max_retries: int = 3
    
    # Delay between retries in seconds
    retry_delay: float = 1.0
    
    # Enable detailed logging
    verbose: bool = False
    
    # Progress monitoring interval in seconds
    monitor_interval: float = 1.0
    
    # Custom task processor settings
    task_processor_config: Dict[str, Any] = None
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.num_bots <= 0:
            raise ValueError("num_bots must be greater than 0")
        
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")
        
        if self.monitor_interval <= 0:
            raise ValueError("monitor_interval must be greater than 0")
        
        if self.task_processor_config is None:
            self.task_processor_config = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'BotConfiguration':
        """Create configuration from dictionary"""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__dataclass_fields__})
    
    @classmethod
    def from_json_file(cls, filepath: str) -> 'BotConfiguration':
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)
    
    @classmethod
    def from_yaml_file(cls, filepath: str) -> 'BotConfiguration':
        """Load configuration from YAML file"""
        with open(filepath, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls.from_dict(config_dict)
    
    def save_json(self, filepath: str):
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def save_yaml(self, filepath: str):
        """Save configuration to YAML file"""
        with open(filepath, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)


class ConfigurationManager:
    """Manages configuration loading and validation"""
    
    @staticmethod
    def load_config(
        filepath: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None
    ) -> BotConfiguration:
        """
        Load configuration from file or dictionary
        
        Args:
            filepath: Path to configuration file (JSON or YAML)
            config_dict: Configuration dictionary
            
        Returns:
            BotConfiguration object
        """
        if filepath:
            path = Path(filepath)
            if not path.exists():
                raise FileNotFoundError(f"Configuration file not found: {filepath}")
            
            if path.suffix in ['.json']:
                return BotConfiguration.from_json_file(filepath)
            elif path.suffix in ['.yaml', '.yml']:
                return BotConfiguration.from_yaml_file(filepath)
            else:
                raise ValueError(f"Unsupported configuration file format: {path.suffix}")
        
        elif config_dict:
            return BotConfiguration.from_dict(config_dict)
        
        else:
            # Return default configuration
            return BotConfiguration()
    
    @staticmethod
    def create_default_config(filepath: str, format: str = 'json'):
        """
        Create a default configuration file
        
        Args:
            filepath: Path where configuration file will be created
            format: File format ('json' or 'yaml')
        """
        config = BotConfiguration()
        
        if format == 'json':
            config.save_json(filepath)
        elif format in ['yaml', 'yml']:
            config.save_yaml(filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")
