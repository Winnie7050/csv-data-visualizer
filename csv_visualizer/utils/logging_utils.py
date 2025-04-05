"""
Logging utilities for CSV Data Visualizer.

This module contains utilities for setting up logging.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging for the application.

    Args:
        log_level: Logging level (default: INFO)

    Returns:
        Logger instance
    """
    # Create logger
    logger = logging.getLogger("csv_visualizer")
    logger.setLevel(log_level)
    
    # Check if handlers are already configured (to avoid duplicate handlers)
    if logger.handlers:
        return logger
    
    # Create logs directory
    logs_dir = _get_logs_directory()
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"csv_visualizer_{timestamp}.log")
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Also add a rotating file handler for app.log that keeps history
    rotating_log = os.path.join(logs_dir, "app.log")
    rotating_handler = logging.handlers.RotatingFileHandler(
        rotating_log,
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=3
    )
    rotating_handler.setLevel(log_level)
    rotating_handler.setFormatter(formatter)
    logger.addHandler(rotating_handler)
    
    logger.info("Logging initialized")
    
    return logger


def _get_logs_directory() -> str:
    """
    Get the logs directory.

    Returns:
        Path to logs directory
    """
    # Check for app data directory first
    app_data = None
    app_name = "CSV Data Visualizer"
    
    if os.name == "nt":  # Windows
        app_data = os.environ.get("APPDATA")
        if app_data:
            logs_dir = os.path.join(app_data, app_name, "logs")
            return logs_dir
    
    # Fall back to the module directory
    module_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    logs_dir = os.path.join(module_dir, "logs")
    return logs_dir


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter for adding contextual information to log records.
    
    This adapter adds a prefix to log messages for better context tracking.
    """
    
    def __init__(self, logger: logging.Logger, prefix: str):
        """
        Initialize the logger adapter.
        
        Args:
            logger: The logger to adapt
            prefix: Prefix to add to messages
        """
        super().__init__(logger, {})
        self.prefix = prefix
    
    def process(self, msg, kwargs):
        """
        Process the log message and add the prefix.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments
            
        Returns:
            Processed message and keyword arguments
        """
        return f"[{self.prefix}] {msg}", kwargs


def get_module_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        module_name: Name of the module
        
    Returns:
        Logger instance
    """
    # Get the base logger
    logger = logging.getLogger("csv_visualizer")
    
    # Create an adapter with module name as prefix
    return LoggerAdapter(logger, module_name)
