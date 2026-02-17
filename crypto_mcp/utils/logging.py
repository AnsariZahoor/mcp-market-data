"""
Centralized logging configuration for Crypto MCP Server.
Provides consistent logging setup across all modules.
"""
import logging
import sys
from typing import Optional


# Global logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(levelname)s - [%(name)s:%(filename)s:%(lineno)d] - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Flag to ensure we only configure once
_configured = False


def configure_logging(
    level: int = LOG_LEVEL,
    format_string: str = LOG_FORMAT,
    date_format: str = DATE_FORMAT
) -> None:
    """
    Configure global logging settings.
    Should be called once at application startup.
    """
    global _configured
    
    if _configured:
        return
    
    logging.basicConfig(
        level=level,
        format=format_string,
        datefmt=date_format,
        stream=sys.stderr,
        force=True
    )
    
    _configured = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance with consistent configuration."""
    if not _configured:
        configure_logging()
    
    return logging.getLogger(name)


def set_level(level: int) -> None:
    """Change the logging level for all loggers."""
    logging.root.setLevel(level)
    

def set_module_level(module_name: str, level: int) -> None:
    """Set logging level for a specific module."""
    logging.getLogger(module_name).setLevel(level)
