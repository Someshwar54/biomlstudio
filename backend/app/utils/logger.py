"""
Logging configuration and utilities
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Optional

from app.core.config import settings


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "detailed",
    log_file: Optional[str] = None
) -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level
        log_format: Format style (simple, detailed, json)
        log_file: Optional log file path
    """
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Format configurations
    formats = {
        "simple": "%(levelname)s - %(message)s",
        "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "json": '{"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
    }
    
    format_string = formats.get(log_format, formats["detailed"])
    
    # Handler configurations
    handlers = ['console']
    if log_file:
        handlers.append('file')
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': format_string,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
        },
        'handlers': {
            'console': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'stream': sys.stdout
            }
        },
        'loggers': {
            'app': {
                'level': log_level,
                'handlers': handlers,
                'propagate': False,
            },
            'celery': {
                'level': log_level,
                'handlers': handlers,
                'propagate': False,
            },
            'uvicorn': {
                'level': log_level,
                'handlers': handlers,
                'propagate': False,
            },
            'sqlalchemy.engine': {
                'level': 'WARNING',
                'handlers': handlers,
                'propagate': False,
            }
        },
        'root': {
            'level': log_level,
            'handlers': handlers,
        }
    }
    
    # Add file handler if log file specified
    if log_file:
        config['handlers']['file'] = {
            'level': log_level,
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': log_file,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }
    
    logging.config.dictConfig(config)


def get_task_logger(name: str) -> logging.Logger:
    """
    Get logger for Celery tasks.
    
    Args:
        name: Logger name
        
    Returns:
        Logger: Configured logger
    """
    logger = logging.getLogger(name)
    
    # Add task-specific formatting if in Celery context
    try:
        from celery import current_task
        
        if current_task and current_task.request:
            task_id = current_task.request.id
            
            # Create custom formatter with task ID
            formatter = logging.Formatter(
                f'%(asctime)s - TASK[{task_id}] - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Update handler formatters
            for handler in logger.handlers:
                handler.setFormatter(formatter)
                
    except ImportError:
        # Not in Celery context, use regular logger
        pass
    
    return logger


def log_function_call(func_name: str, args: tuple, kwargs: dict) -> None:
    """
    Log function call details.
    
    Args:
        func_name: Name of function being called
        args: Function arguments
        kwargs: Function keyword arguments
    """
    logger = logging.getLogger(__name__)
    
    # Sanitize sensitive information
    sanitized_kwargs = {}
    sensitive_keys = ['password', 'token', 'key', 'secret']
    
    for key, value in kwargs.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized_kwargs[key] = '***REDACTED***'
        else:
            sanitized_kwargs[key] = value
    
    logger.debug(f"Calling {func_name} with args={args}, kwargs={sanitized_kwargs}")


def log_performance(func_name: str, duration: float, success: bool = True) -> None:
    """
    Log performance metrics.
    
    Args:
        func_name: Name of function
        duration: Execution duration in seconds
        success: Whether function executed successfully
    """
    logger = logging.getLogger(__name__)
    
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"PERFORMANCE - {func_name} - {status} - {duration:.3f}s")


class ContextualLogger:
    """Logger with contextual information"""
    
    def __init__(self, name: str, context: Dict[str, str]):
        self.logger = logging.getLogger(name)
        self.context = context
    
    def _format_message(self, message: str) -> str:
        """Add context to log message"""
        context_str = " ".join([f"{k}={v}" for k, v in self.context.items()])
        return f"[{context_str}] {message}"
    
    def debug(self, message: str) -> None:
        self.logger.debug(self._format_message(message))
    
    def info(self, message: str) -> None:
        self.logger.info(self._format_message(message))
    
    def warning(self, message: str) -> None:
        self.logger.warning(self._format_message(message))
    
    def error(self, message: str) -> None:
        self.logger.error(self._format_message(message))
    
    def critical(self, message: str) -> None:
        self.logger.critical(self._format_message(message))


# Initialize logging with settings
if hasattr(settings, 'LOG_LEVEL'):
    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_format=getattr(settings, 'LOG_FORMAT', 'detailed'),
        log_file='logs/biomlstudio.log'
    )
