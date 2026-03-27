"""Contract tests for IWebcamService interface."""

from unittest.mock import MagicMock, Mock

import pytest

from src.services.webcam_service import (
    IWebcamService,
    WebcamNotFoundError,
    WebcamNotStartedError,
)


class MockWebcamService(IWebcamService):
    """Mock implementation of IWebcamService for testing."""

    def __init__(self):
        self._running = False
        self._cap = None

    def start(self) -> None:
        """Start the webcam video feed."""
        # Simulate webcam not found
        if not hasattr(self, "_mock_has_webcam") or not self._mock_has_webcam:
            raise WebcamNotFoundError("No webcam available")

        self._cap = MagicMock()
        self._cap.set = Mock()
        self._running = True

    def stop(self) -> None:
        """Stop the webcam video feed and release resources."""
        if not self._running:
            raise WebcamNotStartedError("Webcam is not started")

        if self._cap:
            self._cap.release()
        self._running = False

    def capture_frame(self) -> bytes:
        """Capture the current video frame."""
        if not self._running:
            raise WebcamNotStartedError("Webcam is not started")

        # Return mock JPEG data
        return b"fake_jpeg_data"

    def is_running(self) -> bool:
        """Check if the webcam is currently running."""
        return self._running


class TestWebcamServiceContract:
    """Contract tests for IWebcamService interface."""

    def test_start_success(self):
        """Verify start() initializes webcam without errors."""
        service = MockWebcamService()
        service._mock_has_webcam = True

        service.start()

        assert service.is_running() is True

    def test_start_no_webcam(self):
        """Verify WebcamNotFoundError when no webcam available."""
        service = MockWebcamService()
        service._mock_has_webcam = False

        with pytest.raises(WebcamNotFoundError):
            service.start()

    def test_capture_frame(self):
        """Verify capture_frame() returns valid JPEG data."""
        service = MockWebcamService()
        service._mock_has_webcam = True
        service.start()

        result = service.capture_frame()

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_stop(self):
        """Verify stop() releases webcam resources."""
        service = MockWebcamService()
        service._mock_has_webcam = True
        service.start()
        service.stop()

        assert service.is_running() is False

    def test_stop_before_start_raises_error(self):
        """Verify WebcamNotStartedError when stop() called before start()."""
        service = MockWebcamService()

        with pytest.raises(WebcamNotStartedError):
            service.stop()

    def test_capture_frame_before_start_raises_error(self):
        """Verify WebcamNotStartedError when capture_frame() called before start()."""
        service = MockWebcamService()

        with pytest.raises(WebcamNotStartedError):
            service.capture_frame()
