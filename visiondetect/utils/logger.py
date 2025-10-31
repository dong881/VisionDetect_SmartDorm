"""
Logging utility module
Provides structured logging with file and console output
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class Logger:
    """Custom logger with file and console handlers"""
    
    def __init__(
        self,
        name: str,
        log_dir: str = "LOG",
        log_level: str = "INFO",
        console_output: bool = True
    ):
        """
        Initialize logger
        
        Args:
            name: Logger name
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_output: Whether to output to console
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Avoid adding handlers multiple times
        if self.logger.handlers:
            return
        
        # Create log directory
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler for all logs
        all_log_file = log_path / f"visiondorm_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(all_log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # File handler for errors only
        error_log_file = log_path / f"visiondorm_error_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(simple_formatter)
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, **kwargs)


# Global logger instance
_logger_instance: Optional[Logger] = None


def get_logger(
    name: str = "VisionDetect",
    log_dir: str = "LOG",
    log_level: str = "INFO"
) -> Logger:
    """
    Get global logger instance
    
    Args:
        name: Logger name (only used on first call)
        log_dir: Log directory (only used on first call)
        log_level: Log level (only used on first call)
        
    Returns:
        Logger instance
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = Logger(name, log_dir, log_level)
    
    return _logger_instance
