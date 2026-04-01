"""Utility functions for application logging."""

import logging
from pathlib import Path
from typing import Optional

from src.lib.error_manager import ErrorManager


class LoggerManager:
    """Manages application logging configuration and access.
    
    Provides consistent logging across the application with
    appropriate log levels and file output.
    """
    
    _logger: Optional[logging.Logger] = None
    
    @classmethod
    def get_logger(cls, name: str = "webcam2file") -> logging.Logger:
        """Get or create the application logger.
        
        Args:
            name: Logger name (default: 'webcam2file')
        
        Returns:
            Configured logger instance
        """
        if cls._logger is None:
            cls._logger = logging.getLogger(name)
            cls._logger.setLevel(logging.DEBUG)
        
            # Create console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
        
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
        
            # Add handler to logger
            cls._logger.addHandler(console_handler)
        
        return cls._logger
    
    @classmethod
    def setup_file_logging(
        cls,
        log_dir: str = "logs",
        log_level: int = logging.DEBUG
    ) -> None:
        """Setup file-based logging.
        
        Args:
            log_dir: Directory for log files (default: 'logs')
            log_level: Logging level (default: DEBUG)
        """
        logger = cls.get_logger()
        
        # Create log directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Create file handler
        log_file = log_path / "application.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
    
    @classmethod
    def set_log_level(cls, level: int) -> None:
        """Set the logging level.
        
        Args:
            level: Logging level (e.g., logging.DEBUG, logging.INFO)
        """
        logger = cls.get_logger()
        logger.setLevel(level)
        
        # Update all handlers
        for handler in logger.handlers:
            handler.setLevel(level)


# Error manager for consistent error logging
_error_manager = ErrorManager()


# Convenience functions for direct use
def log_capture_event(filepath: str, filesize: int) -> None:
    """Log a capture event.
    
    Args:
        filepath: Path to the captured image
        filesize: Size of the captured image in bytes
    """
    logger = LoggerManager.get_logger()
    logger.info(f"Image captured: {filepath} ({filesize} bytes)")


def log_file_save(filepath: str, success: bool = True) -> None:
    """Log a file save operation.
    
    Args:
        filepath: Path to the saved file
        success: Whether the save was successful
    """
    logger = LoggerManager.get_logger()
    if success:
        logger.info(f"File saved: {filepath}")
    else:
        logger.error(f"Failed to save file: {filepath}")


def log_error(message: str, context: Optional[dict] = None) -> None:
    """Log an error with optional context.
    
    Args:
        message: Error message
        context: Optional dictionary of context information
    """
    logger = LoggerManager.get_logger()
    if context:
        logger.error(f"{message} | Context: {context}")
    else:
        logger.error(message)


def log_error_with_context(
    error: Exception,
    operation: str,
    context: Optional[dict] = None
) -> None:
    """Log an error with full context including error type and message.
    
    Args:
        error: The exception that occurred
        operation: Description of the operation being performed
        context: Optional dictionary of context information
    """
    logger = LoggerManager.get_logger()
    error_type = type(error).__name__
    error_msg = str(error)
    
    log_entry = f"Error during {operation}: [{error_type}] {error_msg}"
    if context:
        log_entry += f" | Context: {context}"
    
    logger.error(log_entry)


def log_error_with_recovery(
    error: Exception,
    operation: str,
    context: Optional[dict] = None
) -> None:
    """Log an error with recovery action information.
    
    Args:
        error: The exception that occurred
        operation: Description of the operation being performed
        context: Optional dictionary of context information
    """
    logger = LoggerManager.get_logger()
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Get recovery action from error manager
    error_info = _error_manager.handle_error(error)
    recovery_action = error_info['recovery_action']
    
    log_entry = f"Error during {operation}: [{error_type}] {error_msg}"
    if context:
        log_entry += f" | Context: {context}"
    log_entry += f" | Recovery: {recovery_action}"
    
    logger.error(log_entry)


def log_processing_start(filepath: str) -> None:
    """Log the start of processing.
    
    Args:
        filepath: Path to the file being processed
    """
    logger = LoggerManager.get_logger()
    logger.info(f"Processing started: {filepath}")


def log_processing_complete(filepath: str) -> None:
    """Log processing completion.
    
    Args:
        filepath: Path to the processed file
    """
    logger = LoggerManager.get_logger()
    logger.info(f"Processing completed: {filepath}")


def log_comfyui_api_call(endpoint: str, success: bool = True) -> None:
    """Log a ComfyUI API call.
    
    Args:
        endpoint: API endpoint called
        success: Whether the call was successful
    """
    logger = LoggerManager.get_logger()
    if success:
        logger.info(f"ComfyUI API call successful: {endpoint}")
    else:
        logger.error(f"ComfyUI API call failed: {endpoint}")


def log_queue_operation(operation: str, queue_size: int) -> None:
    """Log a queue operation.
    
    Args:
        operation: Description of the operation
        queue_size: Current queue size
    """
    logger = LoggerManager.get_logger()
    logger.debug(f"Queue operation: {operation} | Size: {queue_size}")


def log_retry_attempt(operation: str, attempt: int, max_attempts: int) -> None:
    """Log a retry attempt for transient failures.
    
    Args:
        operation: Description of the operation being retried
        attempt: Current attempt number (1-indexed)
        max_attempts: Maximum number of retry attempts
    """
    logger = LoggerManager.get_logger()
    logger.warning(
        f"Retry attempt {attempt}/{max_attempts} for {operation}"
    )


def log_retry_success(operation: str, attempt: int) -> None:
    """Log successful completion after retry.
    
    Args:
        operation: Description of the operation
        attempt: Number of attempts it took to succeed
    """
    logger = LoggerManager.get_logger()
    logger.info(
        f"{operation} succeeded on attempt {attempt}"
    )


def log_retry_exhausted(operation: str, max_attempts: int) -> None:
    """Log when all retry attempts have been exhausted.
    
    Args:
        operation: Description of the operation
        max_attempts: Maximum number of retry attempts
    """
    logger = LoggerManager.get_logger()
    logger.error(
        f"{operation} failed after {max_attempts} attempts"
    )


def log_recovery_action(operation: str, action: str) -> None:
    """Log a recovery action being taken.
    
    Args:
        operation: Description of the operation
        action: The recovery action being taken
    """
    logger = LoggerManager.get_logger()
    logger.info(f"Recovery action for {operation}: {action}")


def log_webcam_error(error: Exception, operation: str) -> None:
    """Log a webcam-related error with user-friendly message.
    
    Args:
        error: The exception that occurred
        operation: Description of the operation being performed
    """
    logger = LoggerManager.get_logger()
    error_info = _error_manager.handle_error(error)
    logger.error(
        f"Webcam error during {operation}: {error_info['user_message']} | "
        f"Recovery: {error_info['recovery_action']}"
    )


def log_api_error(error: Exception, operation: str) -> None:
    """Log a ComfyUI API error with user-friendly message.
    
    Args:
        error: The exception that occurred
        operation: Description of the operation being performed
    """
    logger = LoggerManager.get_logger()
    error_info = _error_manager.handle_error(error)
    logger.error(
        f"API error during {operation}: {error_info['user_message']} | "
        f"Recovery: {error_info['recovery_action']}"
    )
