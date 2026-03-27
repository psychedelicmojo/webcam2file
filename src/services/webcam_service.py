"""Interface for webcam video capture operations."""

from abc import ABC, abstractmethod


class WebcamNotFoundError(Exception):
    """Raised when no webcam is available."""

    pass


class WebcamAccessError(Exception):
    """Raised when webcam access is denied."""

    pass


class WebcamNotStartedError(Exception):
    """Raised when webcam is not started."""

    pass


class CaptureError(Exception):
    """Raised when frame capture fails."""

    pass


class IWebcamService(ABC):
    """Interface for webcam video capture operations."""

    @abstractmethod
    def start(self) -> None:
        """Start the webcam video feed.

        Raises:
            WebcamNotFoundError: If no webcam is available.
            WebcamAccessError: If webcam access is denied.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the webcam video feed and release resources."""
        pass

    @abstractmethod
    def capture_frame(self) -> bytes:
        """Capture the current video frame.

        Returns:
            bytes: JPEG-encoded image data.

        Raises:
            WebcamNotStartedError: If start() was not called.
            CaptureError: If frame capture fails.
        """
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if the webcam is currently running.

        Returns:
            bool: True if running, False otherwise.
        """
        pass
