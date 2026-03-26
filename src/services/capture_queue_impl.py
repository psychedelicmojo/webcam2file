"""Implementation of ICaptureQueue with thread-safe queue for processing images."""

import threading
from typing import Optional

from src.services.capture_queue import ICaptureQueue, ProcessingState


class QueueFullError(Exception):
    """Raised when the queue is full and cannot accept more items."""
    pass


class CaptureQueue(ICaptureQueue):
    """Implementation of ICaptureQueue with thread-safe queue for processing images.
    
    This service manages a queue of images to be processed through ComfyUI.
    It provides thread-safe operations for enqueueing, dequeueing, and state management.
    The queue processes images in FIFO order and handles concurrent captures gracefully.
    """

    def __init__(self, max_size: int = 100):
        """Initialize the capture queue.
        
        Args:
            max_size: Maximum number of items in the queue (default: 100).
                     Use 0 for unlimited size.
        """
        self._queue: list[str] = []
        self._max_size = max_size
        self._lock = threading.RLock()
        self._state = ProcessingState.IDLE
        self._error_message: Optional[str] = None
        self._current_image: Optional[str] = None

    def enqueue(self, image_path: str) -> None:
        """Add an image to the processing queue.
        
        Args:
            image_path: Path to the image to process.
        
        Raises:
            QueueFullError: If the queue is full and max_size is set.
        """
        with self._lock:
            # Check if queue is full
            if self._max_size > 0 and len(self._queue) >= self._max_size:
                raise QueueFullError("Queue is full")

            # Add to queue
            self._queue.append(image_path)

    def dequeue(self) -> Optional[str]:
        """Remove and return the next image from the queue.
        
        Returns:
            Optional[str]: Path to the next image, or None if queue is empty.
        """
        with self._lock:
            if not self._queue:
                return None

            return self._queue.pop(0)

    def get_queue_size(self) -> int:
        """Get the current queue size.
        
        Returns:
            int: Number of images waiting in queue.
        """
        with self._lock:
            return len(self._queue)

    def get_processing_state(self) -> ProcessingState:
        """Get the current processing state.
        
        Returns:
            ProcessingState: Current state of processing.
        """
        with self._lock:
            return self._state

    def set_processing_state(
        self,
        state: ProcessingState,
        error_message: Optional[str] = None
    ) -> None:
        """Set the current processing state.
        
        Args:
            state: New processing state.
            error_message: Error message if state is ERROR.
        """
        with self._lock:
            self._state = state
            if state == ProcessingState.ERROR:
                self._error_message = error_message
            else:
                self._error_message = None

    def is_processing(self) -> bool:
        """Check if processing is currently active.
        
        Returns:
            bool: True if processing, False otherwise.
        """
        with self._lock:
            return self._state == ProcessingState.PROCESSING

    def get_current_image(self) -> Optional[str]:
        """Get the path of the image currently being processed.
        
        Returns:
            Optional[str]: Path to the current image, or None if not processing.
        """
        with self._lock:
            return self._current_image

    def set_current_image(self, image_path: Optional[str]) -> None:
        """Set the path of the image currently being processed.
        
        Args:
            image_path: Path to the current image, or None to clear.
        """
        with self._lock:
            self._current_image = image_path

    def get_error_message(self) -> Optional[str]:
        """Get the current error message.
        
        Returns:
            Optional[str]: Error message if state is ERROR, None otherwise.
        """
        with self._lock:
            return self._error_message

    def clear(self) -> None:
        """Clear all items from the queue."""
        with self._lock:
            self._queue.clear()
            self._state = ProcessingState.IDLE
            self._error_message = None
            self._current_image = None

    def is_empty(self) -> bool:
        """Check if the queue is empty.
        
        Returns:
            bool: True if queue is empty, False otherwise.
        """
        with self._lock:
            return len(self._queue) == 0

    def is_full(self) -> bool:
        """Check if the queue is full.
        
        Returns:
            bool: True if queue is full, False otherwise.
        """
        with self._lock:
            if self._max_size <= 0:
                return False
            return len(self._queue) >= self._max_size

    def peek(self) -> Optional[str]:
        """Get the next item in the queue without removing it.
        
        Returns:
            Optional[str]: Path to the next image, or None if queue is empty.
        """
        with self._lock:
            if not self._queue:
                return None
            return self._queue[0]

    def remove(self, image_path: str) -> bool:
        """Remove a specific image from the queue.
        
        Args:
            image_path: Path to the image to remove.
        
        Returns:
            bool: True if removed successfully, False if not found.
        """
        with self._lock:
            if image_path in self._queue:
                self._queue.remove(image_path)
                return True
            return False

    def get_all_items(self) -> list[str]:
        """Get all items in the queue.
        
        Returns:
            list[str]: List of all image paths in the queue.
        """
        with self._lock:
            return list(self._queue)
