"""
Logging configuration for LED Panel Display System.

Provides structured logging with appropriate levels and formatting.
"""
import logging
import sys


def setup_logging(level=logging.INFO):
    """
    Configure logging for the LED panel system.
    
    Args:
        level: Logging level (default: INFO)
    """
    # Create logger
    logger = logging.getLogger('led_panel')
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '[%(levelname)-8s] %(name)s: %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


def get_logger(name):
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f'led_panel.{name}')


# Initialize root logger
setup_logging()

