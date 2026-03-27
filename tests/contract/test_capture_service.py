"""Contract tests for CaptureService interface."""

from pathlib import Path

import pytest

from src.models.image_capture import ImageCapture
from src.services.capture_service import CaptureService
from src.services.visual_feedback import IVisualFeedback
from src.services.webcam_service import IWebcamService


class MockWebcamService(IWebcamService):
    """Mock implementation of IWebcamService for testing."""

    def __init__(self):
        self._running = False
        self._mock_frame_data = b"fake_jpeg_data"

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        if not self._running:
            raise Exception("Webcam is not started")
        self._running = False

    def capture_frame(self) -> bytes:
        if not self._running:
            raise Exception("Webcam is not started")
        return self._mock_frame_data

    def is_running(self) -> bool:
        return self._running


class MockVisualFeedback(IVisualFeedback):
    """Mock implementation of IVisualFeedback for testing."""

    def __init__(self):
        self._current_effect = ""
        self.show_capture_called = False
        self.hide_called = False

    def show_capture_feedback(self) -> None:
        self._current_effect = "capture"
        self.show_capture_called = True

    def show_processing_feedback(self) -> None:
        self._current_effect = "processing"

    def show_completion_feedback(self) -> None:
        self._current_effect = "completion"

    def show_error_feedback(self, message: str) -> None:
        self._current_effect = "error"

    def hide_feedback(self) -> None:
        self._current_effect = ""
        self.hide_called = True

    def get_current_effect(self) -> str:
        return self._current_effect


class TestCaptureServiceContract:
    """Contract tests for CaptureService."""

    def test_capture_success(self):
        """Verify capture() successfully captures and saves an image."""
        # Setup mocks
        webcam_service = MockWebcamService()
        webcam_service.start()
        visual_feedback = MockVisualFeedback()

        # Create temporary output folder
        import tempfile

        with tempfile.TemporaryDirectory() as output_folder:
            service = CaptureService(
                webcam_service=webcam_service,
                visual_feedback=visual_feedback,
                output_folder=output_folder,
            )

            # Capture image
            result = service.capture()

            # Verify results
            assert isinstance(result, ImageCapture)
            assert result.status == "pending"
            assert result.filepath.endswith(".jpg")
            assert Path(result.filepath).exists()
            assert result.filesize > 0
            assert result.output_folder == output_folder

    def test_capture_with_feedback(self):
        """Verify capture() shows visual feedback."""
        webcam_service = MockWebcamService()
        webcam_service.start()
        visual_feedback = MockVisualFeedback()

        import tempfile

        with tempfile.TemporaryDirectory() as output_folder:
            service = CaptureService(
                webcam_service=webcam_service,
                visual_feedback=visual_feedback,
                output_folder=output_folder,
            )

            service.capture()

            # Verify feedback was shown
            assert visual_feedback.show_capture_called is True
            assert visual_feedback.hide_called is True

    def test_capture_webcam_not_started_raises_error(self):
        """Verify CaptureError when webcam is not started."""
        webcam_service = MockWebcamService()
        visual_feedback = MockVisualFeedback()

        import tempfile

        with tempfile.TemporaryDirectory() as output_folder:
            service = CaptureService(
                webcam_service=webcam_service,
                visual_feedback=visual_feedback,
                output_folder=output_folder,
            )

            with pytest.raises(Exception):
                service.capture()

    def test_capture_generates_unique_filename(self):
        """Verify capture() generates unique filenames."""
        import time

        webcam_service = MockWebcamService()
        webcam_service.start()
        visual_feedback = MockVisualFeedback()

        import tempfile

        with tempfile.TemporaryDirectory() as output_folder:
            service = CaptureService(
                webcam_service=webcam_service,
                visual_feedback=visual_feedback,
                output_folder=output_folder,
            )

            # Capture multiple images with a small delay
            capture1 = service.capture()
            time.sleep(1.1)  # Wait for timestamp to change
            capture2 = service.capture()

            # Verify filenames are different
            assert capture1.filepath != capture2.filepath
            assert capture1.timestamp != capture2.timestamp
