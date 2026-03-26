"""Interface for monitoring a folder for new files."""

from abc import ABC, abstractmethod
from typing import Callable


class FolderNotFoundError(Exception):
    """Raised when the folder does not exist."""
    pass


class FolderAccessError(Exception):
    """Raised when folder access is denied."""
    pass


class IFileMonitorService(ABC):
    """Interface for monitoring a folder for new files."""

    @abstractmethod
    def start_monitoring(
        self,
        folder_path: str,
        on_file_created: Callable[[str], None]
    ) -> None:
        """Start monitoring a folder for new files.
        
        Args:
            folder_path: Path to the folder to monitor.
            on_file_created: Callback function called when a new file is created.
                           Receives the full file path as argument.
                           
        Raises:
            FolderNotFoundError: If the folder does not exist.
            FolderAccessError: If folder access is denied.
        """
        pass

    @abstractmethod
    def stop_monitoring(self) -> None:
        """Stop monitoring the folder."""
        pass

    @abstractmethod
    def is_monitoring(self) -> bool:
        """Check if monitoring is currently active.
        
        Returns:
            bool: True if monitoring, False otherwise.
        """
        pass
