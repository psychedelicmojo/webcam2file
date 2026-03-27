"""Implementation of IFileMonitorService using watchdog for file system monitoring."""

import time
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.services.file_monitor_service import (
    FolderAccessError,
    FolderNotFoundError,
    IFileMonitorService,
)


class FileMonitorHandler(FileSystemEventHandler):
    """Custom file system event handler for monitoring new file creation."""

    def __init__(
        self,
        on_file_created: Callable[[str], None],
        file_extensions: Optional[list] = None,
    ):
        """Initialize the file monitor handler.

        Args:
            on_file_created: Callback function called when a new file is created.
                           Receives the full file path as argument.
            file_extensions: List of file extensions to monitor (default: ['.jpg', '.jpeg']).
                           If None, monitors all files.
        """
        super().__init__()
        self._on_file_created = on_file_created
        self._file_extensions = file_extensions or [".jpg", ".jpeg"]
        self._last_event_time = 0
        self._debounce_delay = 0.5  # seconds

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events.

        Args:
            event: The file system event object.
        """
        current_time = time.time()

        # Debounce rapid events (e.g., from file copy operations)
        if current_time - self._last_event_time < self._debounce_delay:
            return

        self._last_event_time = current_time

        # Skip directory creation events
        if event.is_directory:
            return

        # Check if file has a monitored extension
        src_path = event.src_path
        file_ext = Path(src_path).suffix.lower()

        if file_ext in self._file_extensions:
            self._on_file_created(src_path)


class FileMonitorServiceImpl(IFileMonitorService):
    """Implementation of IFileMonitorService using watchdog for file system monitoring.

    This service monitors a folder for new JPEG files and triggers callbacks when
    files are created. It handles file system race conditions and filters for
    specific file types.
    """

    def __init__(self, file_extensions: Optional[list] = None):
        """Initialize the file monitor service.

        Args:
            file_extensions: List of file extensions to monitor (default: ['.jpg', '.jpeg']).
                           If None, monitors all files.
        """
        self._observer: Optional[Observer] = None
        self._handler: Optional[FileMonitorHandler] = None
        self._monitoring = False
        self._folder_path: Optional[str] = None
        self._file_extensions = file_extensions or [".jpg", ".jpeg"]

    def start_monitoring(
        self, folder_path: str, on_file_created: Callable[[str], None]
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
        path = Path(folder_path)

        # Check if folder exists
        if not path.exists():
            raise FolderNotFoundError(f"Folder does not exist: {folder_path}")

        # Check if folder is accessible
        if not path.is_dir():
            raise FolderNotFoundError(f"Path is not a directory: {folder_path}")

        try:
            # Try to list directory contents to verify access
            list(path.iterdir())
        except PermissionError:
            raise FolderAccessError(f"Cannot access folder: {folder_path}")
        except OSError as e:
            raise FolderAccessError(f"Cannot access folder: {folder_path} - {str(e)}")

        # Store folder path
        self._folder_path = folder_path

        # Create handler with callback
        self._handler = FileMonitorHandler(on_file_created, self._file_extensions)

        # Create and start observer
        self._observer = Observer()
        self._observer.schedule(self._handler, str(path), recursive=False)
        self._observer.start()

        self._monitoring = True

    def stop_monitoring(self) -> None:
        """Stop monitoring the folder.

        Shuts down the observer and releases resources.
        """
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2.0)
            self._observer = None

        self._handler = None
        self._monitoring = False
        self._folder_path = None

    def is_monitoring(self) -> bool:
        """Check if monitoring is currently active.

        Returns:
            bool: True if monitoring, False otherwise.
        """
        return self._monitoring and self._observer is not None

    @property
    def folder_path(self) -> Optional[str]:
        """Get the currently monitored folder path.

        Returns:
            Optional[str]: The folder path being monitored, or None if not monitoring.
        """
        return self._folder_path

    @property
    def file_extensions(self) -> list:
        """Get the file extensions being monitored.

        Returns:
            list: List of file extensions being monitored.
        """
        return self._file_extensions
