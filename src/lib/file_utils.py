"""Utility functions for file operations."""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


class FileUtils:
    """Utility class for file operations.
    
    Handles file system operations with proper error handling
    and race condition management.
    """
    
    @staticmethod
    def generate_unique_filename(
        prefix: str = 'capture',
        suffix: str = '.jpg'
    ) -> str:
        """Generate a unique filename with timestamp.
        
        Args:
            prefix: Filename prefix (default: 'capture')
            suffix: Filename suffix (default: '.jpg')
            
        Returns:
            Unique filename in format: prefix_YYYYMMDD_HHmmss.suffix
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}{suffix}"
    
    @staticmethod
    def wait_for_file_ready(
        filepath: str,
        timeout: float = 5.0,
        check_interval: float = 0.1
    ) -> bool:
        """Wait for a file to be fully written and ready.
        
        Handles file system race conditions by checking if the file
        is accessible and has stopped growing.
        
        Args:
            filepath: Path to the file to check.
            timeout: Maximum time to wait in seconds (default: 5).
            check_interval: Time between checks in seconds (default: 0.1).
            
        Returns:
            True if file is ready, False if timeout occurred.
        """
        path = Path(filepath)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check if file exists and is accessible
                if not path.exists():
                    time.sleep(check_interval)
                    continue
                
                # Get file size
                size1 = path.stat().st_size
                
                # Wait a bit
                time.sleep(check_interval)
                
                # Check file size again
                size2 = path.stat().st_size
                
                # If size hasn't changed, file is ready
                if size1 == size2 and size1 > 0:
                    return True
                    
            except (OSError, IOError):
                # File might still be writing, continue waiting
                time.sleep(check_interval)
        
        return False
    
    @staticmethod
    def get_file_size(filepath: str) -> int:
        """Get the size of a file in bytes.
        
        Args:
            filepath: Path to the file.
            
        Returns:
            File size in bytes.
            
        Raises:
            FileNotFoundError: If the file does not exist.
        """
        return Path(filepath).stat().st_size
    
    @staticmethod
    def ensure_directory(directory: str) -> None:
        """Ensure a directory exists, creating it if necessary.
        
        Args:
            directory: Path to the directory.
        """
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def is_file_writable(filepath: str) -> bool:
        """Check if a file is writable.
        
        Args:
            filepath: Path to the file.
            
        Returns:
            True if the file is writable, False otherwise.
        """
        try:
            # Try to open file in append mode to check writability
            with open(filepath, 'a'):
                pass
            return True
        except (OSError, IOError):
            return False
