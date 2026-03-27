"""Interface for managing the capture queue."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


class ProcessingState(Enum):
    """Enum for processing states."""

    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class ICaptureQueue(ABC):
    """Interface for managing the capture queue."""

    @abstractmethod
    def enqueue(self, image_path: str) -> None:
        """Add an image to the processing queue.

        Args:
            image_path: Path to the image to process.
        """
        pass

    @abstractmethod
    def dequeue(self) -> Optional[str]:
        """Remove and return the next image from the queue.

        Returns:
            Optional[str]: Path to the next image, or None if queue is empty.
        """
        pass

    @abstractmethod
    def get_queue_size(self) -> int:
        """Get the current queue size.

        Returns:
            int: Number of images waiting in queue.
        """
        pass

    @abstractmethod
    def get_processing_state(self) -> ProcessingState:
        """Get the current processing state.

        Returns:
            ProcessingState: Current state of processing.
        """
        pass

    @abstractmethod
    def set_processing_state(
        self, state: ProcessingState, error_message: Optional[str] = None
    ) -> None:
        """Set the current processing state.

        Args:
            state: New processing state.
            error_message: Error message if state is ERROR.
        """
        pass

    @abstractmethod
    def is_processing(self) -> bool:
        """Check if processing is currently active.

        Returns:
            bool: True if processing, False otherwise.
        """
        pass
