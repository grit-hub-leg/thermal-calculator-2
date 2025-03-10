# utils/config.py

"""
Configuration management for the Data Center Cooling Calculator.

This module provides utilities for loading, validating, and accessing
configuration settings for the calculator application.
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    # General settings
    "units": "metric",
    "default_location": "europe",
    "include_commercial": True,
    
    # Data directories
    "data_dir": "./data",
    "report_dir": "./reports",
    
    # Logging
    "log_level": "INFO",
    "log_file": "calculator.log",
    
    # Server settings
    "api_host": "0.0.0.0",
    "api_port": 5000,
    "web_host": "0.0.0.0",
    "web_port": 8000,
    
    # Default fluid properties
    "default_fluid": "water",
    "default_glycol_percentage": 0,
    
    # Report generation
    "report_format": "pdf",
    "include_charts": True,
    
    # Validation settings
    "validation_ranges": {
        "cooling_kw": [0, 500],
        "room_temp": [10, 40],
        "desired_temp": [10, 35],
        "water_temp": [5, 30],
        "flow_rate": [0, 50],
        "return_water_temp": [5, 50],
        "fan_speed_percentage": [0, 100],
        "server_air_flow": [0, 20000],
        "server_pressure": [0, 500],
        "glycol_percentage": [0, 60]
    },
    
    # Analytics
    "enable_analytics": False,
    "analytics_storage": "file"  # 'file', 'database'
}

class ConfigManager:
    """
    Configuration manager for the cooling calculator.
    
    This class handles loading, validating, and accessing configuration settings.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
        """
        self.config = DEFAULT_CONFIG.copy()
        
        # Load configuration from file if specified
        if config_path:
            self.load_config(config_path)
            
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        # Validate configuration
        self._validate_config()
        
        # Ensure directories exist
        self._ensure_directories()
    
    def load_config(self, config_path: str) -> bool:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
            
        Returns:
            True if configuration was loaded successfully, False otherwise
        """
        if not os.path.exists(config_path):
            logger.warning(f"Configuration file not found: {config_path}")
            return False
        
        try:
            # Determine file format based on extension
            ext = os.path.splitext(config_path)[1].lower()
            
            if ext in ['.yml', '.yaml']:
                # Load YAML configuration
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
            elif ext in ['.json']:
                # Load JSON configuration
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
            else:
                logger.error(f"Unsupported configuration file format: {ext}")
                return False
            
            # Update configuration with loaded data
            self._update_config(config_data)
            logger.info(f"Configuration loaded from {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return False
    
    def save_config(self, config_path: str) -> bool:
        """
        Save current configuration to file.
        
        Args:
            config_path: Path to save configuration file
            
        Returns:
            True if configuration was saved successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
            
            # Determine file format based on extension
            ext = os.path.splitext(config_path)[1].lower()
            
            if ext in ['.yml', '.yaml']:
                # Save as YAML
                with open(config_path, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
            elif ext in ['.json']:
                # Save as JSON
                with open(config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
            else:
                logger.error(f"Unsupported configuration file format: {ext}")
                return False
            
            logger.info(f"Configuration saved to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default if not found
        """
        # Support nested keys with dot notation (e.g., "server.host")
        if '.' in key:
            parts = key.split('.')
            current = self.config
            
            for part in parts[:-1]:
                current = current.get(part, {})
                if not isinstance(current, dict):
                    return default
            
            return current.get(parts[-1], default)
        
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        # Support nested keys with dot notation (e.g., "server.host")
        if '.' in key:
            parts = key.split('.')
            current = self.config
            
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
            
            current[parts[-1]] = value
        else:
            self.config[key] = value
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Dictionary containing all configuration values
        """
        return self.config.copy()
    
    def reset(self) -> None:
        """Reset configuration to default values."""
        self.config = DEFAULT_CONFIG.copy()
        self._ensure_directories()
    
    def _update_config(self, config_data: Dict[str, Any]) -> None:
        """
        Update configuration with loaded data.
        
        Args:
            config_data: Dictionary containing configuration data
        """
        self._deep_update(self.config, config_data)
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively update a dictionary with another dictionary.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with new values
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # Recursively update nested dictionaries
                self._deep_update(target[key], value)
            else:
                # Update or add value
                target[key] = value
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # Environment variables start with "COOLING_" prefix
        prefix = "COOLING_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert environment variable name to config key
                config_key = key[len(prefix):].lower().replace('__', '.')
                
                # Try to convert value to appropriate type
                try:
                    # First, try to parse as JSON
                    parsed_value = json.loads(value)
                    self.set(config_key, parsed_value)
                except json.JSONDecodeError:
                    # If not valid JSON, use string value
                    self.set(config_key, value)
                
                logger.debug(f"Config override from environment: {config_key}={value}")
    
    def _validate_config(self) -> None:
        """Validate configuration values and types."""
        # Ensure units is either 'metric' or 'imperial'
        units = self.get('units')
        if units not in ['metric', 'imperial']:
            logger.warning(f"Invalid units: {units}, using default: metric")
            self.set('units', 'metric')
        
        # Ensure ports are valid numbers
        for port_key in ['api_port', 'web_port']:
            try:
                port = int(self.get(port_key))
                if port < 1 or port > 65535:
                    raise ValueError("Port out of range")
                self.set(port_key, port)
            except (ValueError, TypeError):
                logger.warning(f"Invalid {port_key}: {self.get(port_key)}, using default")
                self.set(port_key, DEFAULT_CONFIG[port_key])
        
        # Ensure directories have valid paths
        for dir_key in ['data_dir', 'report_dir']:
            dir_path = self.get(dir_key)
            if not isinstance(dir_path, str) or not dir_path:
                logger.warning(f"Invalid {dir_key}: {dir_path}, using default")
                self.set(dir_key, DEFAULT_CONFIG[dir_key])
        
        # Ensure log level is valid
        log_level = self.get('log_level')
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level not in valid_levels:
            logger.warning(f"Invalid log_level: {log_level}, using default: INFO")
            self.set('log_level', 'INFO')
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        for dir_key in ['data_dir', 'report_dir']:
            dir_path = self.get(dir_key)
            os.makedirs(dir_path, exist_ok=True)

# Global configuration instance
config = ConfigManager()

def load_config(config_path: str) -> bool:
    """
    Load configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        True if configuration was loaded successfully, False otherwise
    """
    return config.load_config(config_path)

def get_config(key: str, default: Any = None) -> Any:
    """
    Get configuration value.
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value or default if not found
    """
    return config.get(key, default)

def set_config(key: str, value: Any) -> None:
    """
    Set configuration value.
    
    Args:
        key: Configuration key
        value: Configuration value
    """
    config.set(key, value)

def get_all_config() -> Dict[str, Any]:
    """
    Get all configuration values.
    
    Returns:
        Dictionary containing all configuration values
    """
    return config.get_all()

def reset_config() -> None:
    """Reset configuration to default values."""
    config.reset()

# utils/logging.py

"""
Logging configuration for the Data Center Cooling Calculator.

This module provides functions for setting up and configuring logging
for the calculator application.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any

from utils.config import get_config

# Default log format
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def setup_logging(config_override: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Set up logging for the application.
    
    Args:
        config_override: Optional dictionary to override config settings
        
    Returns:
        Root logger
    """
    # Get configuration settings
    log_level_name = config_override.get('log_level') if config_override else get_config('log_level', 'INFO')
    log_file = config_override.get('log_file') if config_override else get_config('log_file', 'calculator.log')
    log_format = config_override.get('log_format') if config_override else get_config('log_format', DEFAULT_LOG_FORMAT)
    
    # Convert log level name to logging constant
    log_level = getattr(logging, log_level_name.upper(), logging.INFO)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    formatter = logging.Formatter(log_format)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler
    try:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (IOError, PermissionError) as e:
        logger.error(f"Failed to create log file: {e}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

class LoggingContext:
    """
    Context manager for temporarily changing log level.
    
    This class allows temporarily changing the log level for a specific
    section of code using a context manager.
    """
    
    def __init__(self, logger: logging.Logger, level: int):
        """
        Initialize the context manager.
        
        Args:
            logger: Logger instance
            level: New log level
        """
        self.logger = logger
        self.level = level
        self.old_level = logger.level
    
    def __enter__(self) -> logging.Logger:
        """
        Set the new log level.
        
        Returns:
            Logger instance
        """
        self.logger.setLevel(self.level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Restore the original log level."""
        self.logger.setLevel(self.old_level)

def log_function_call(func):
    """
    Decorator for logging function calls.
    
    This decorator logs function calls and return values
    at DEBUG level, and exceptions at ERROR level.
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        
        # Log function call
        args_str = ", ".join([str(arg) for arg in args])
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        params_str = ", ".join(filter(None, [args_str, kwargs_str]))
        
        logger.debug(f"Calling {func.__name__}({params_str})")
        
        try:
            # Call function
            result = func(*args, **kwargs)
            
            # Log return value
            logger.debug(f"{func.__name__} returned: {result}")
            
            return result
        except Exception as e:
            # Log exception
            logger.error(f"Exception in {func.__name__}: {str(e)}", exc_info=True)
            raise
    
    return wrapper

def log_execution_time(func):
    """
    Decorator for logging function execution time.
    
    This decorator logs the execution time of functions
    at DEBUG level.
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        
        # Record start time
        start_time = datetime.now()
        
        try:
            # Call function
            result = func(*args, **kwargs)
            
            # Calculate execution time
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Log execution time
            logger.debug(f"{func.__name__} executed in {execution_time:.3f} seconds")
            
            return result
        except Exception as e:
            # Log exception
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            logger.error(f"{func.__name__} failed after {execution_time:.3f} seconds: {str(e)}", exc_info=True)
            raise
    
    return wrapper
