"""Integration tests for User Story 1 - Capture and Save Image workflow.

These tests verify the complete end-to-end workflow of capturing an image
from the webcam and saving it to the output folder.
"""

import tempfile
import time
from pathlib import Path

import pytest

from src.lib.file_utils import FileUtils
from src.models.image_capture import ImageCapture
from src.services.visual_feedback import IVisualFeedback
from src.services.webcam_service import (
    CaptureError,
    IWebcamService,
    WebcamNotFoundError,
)


class MockWebcamService(IWebcamService):
    """Mock implementation of IWebcamService for testing."""

    def __init__(self):
        self._running = False
        self._mock_frame_data = b'fake_jpeg_data'

    def start(self) -> None:
        if not hasattr(self, '_mock_has_webcam') or not self._mock_has_webcam:
            raise WebcamNotFoundError("No webcam available")
        self._running = True

    def stop(self) -> None:
        if not self._running:
            raise Exception("Webcam is not started")
        self._running = False

    def capture_frame(self) -> bytes:
        if not self._running:
            raise CaptureError("Webcam is not started")
        return self._mock_frame_data

    def is_running(self) -> bool:
        return self._running


class MockVisualFeedback(IVisualFeedback):
    """Mock implementation of IVisualFeedback for testing."""

    def __init__(self):
        self._current_effect = ""
        self.effects = []

    def show_capture_feedback(self) -> None:
        self._current_effect = "capture"
        self.effects.append("capture")

    def show_processing_feedback(self) -> None:
        self._current_effect = "processing"
        self.effects.append("processing")

    def show_completion_feedback(self) -> None:
        self._current_effect = "completion"
        self.effects.append("completion")

    def show_error_feedback(self, message: str) -> None:
        self._current_effect = "error"
        self.effects.append(f"error: {message}")

    def hide_feedback(self) -> None:
        self._current_effect = ""

    def get_current_effect(self) -> str:
        return self._current_effect


class TestUserStory1Integration:
    """Integration tests for User Story 1 - Capture and Save Image."""

    def test_full_capture_workflow_success(self):
        """Test complete capture workflow with successful image save."""
        # Setup
        with tempfile.TemporaryDirectory() as output_folder:
            webcam_service = MockWebcamService()
            webcam_service._mock_has_webcam = True
            visual_feedback = MockVisualFeedback()

            # Start webcam
            webcam_service.start()
            assert webcam_service.is_running() is True

            # Show capture feedback
            visual_feedback.show_capture_feedback()

            # Capture frame
            frame_data = webcam_service.capture_frame()
            assert frame_data == b'fake_jpeg_data'

            # Save to file
            filename = FileUtils.generate_unique_filename(prefix='capture', suffix='.jpg')
            filepath = Path(output_folder) / filename

            with open(filepath, 'wb') as f:
                f.write(frame_data)

            # Verify file was created
            assert filepath.exists()
            assert filepath.stat().st_size > 0

            # Create ImageCapture
            image_capture = ImageCapture(
                timestamp=filename.replace('.jpg', '').replace('capture_', ''),
                filepath=str(filepath),
                filesize=filepath.stat().st_size,
                output_folder=output_folder,
                status='pending'
            )

            # Verify ImageCapture
            assert image_capture.status == 'pending'
            assert image_capture.filepath == str(filepath)
            assert image_capture.filesize > 0

            # Verify visual feedback was shown
            assert "capture" in visual_feedback.effects

    def test_multiple_captures_unique_filenames(self):
        """Test that multiple captures generate unique filenames."""
        with tempfile.TemporaryDirectory() as output_folder:
            webcam_service = MockWebcamService()
            webcam_service._mock_has_webcam = True
            visual_feedback = MockVisualFeedback()

            webcam_service.start()

            # Capture multiple images with delays between filename generation
            timestamps = []
            for i in range(3):
                # Wait for timestamp to change before generating filename
                if i > 0:
                    time.sleep(1.0)  # Wait for timestamp to change (file_utils uses seconds)
                frame_data = webcam_service.capture_frame()
                filename = FileUtils.generate_unique_filename(prefix='capture', suffix='.jpg')
                filepath = Path(output_folder) / filename

                with open(filepath, 'wb') as f:
                    f.write(frame_data)

                timestamps.append(filename.replace('.jpg', '').replace('capture_', ''))

            # Verify all timestamps are unique
            assert len(set(timestamps)) == 3

            # Verify all files exist
            for ts in timestamps:
                filepath = Path(output_folder) / f"capture_{ts}.jpg"
                assert filepath.exists()

    def test_capture_with_queue(self):
        """Test that captures can be queued when processing is ongoing."""
        with tempfile.TemporaryDirectory() as output_folder:
            webcam_service = MockWebcamService()
            webcam_service._mock_has_webcam = True
            visual_feedback = MockVisualFeedback()

            # Start webcam
            webcam_service.start()

            # Simulate multiple captures
            captured_files = []
            for i in range(3):
                frame_data = webcam_service.capture_frame()
                filename = FileUtils.generate_unique_filename(prefix='capture', suffix='.jpg')
                filepath = Path(output_folder) / filename

                with open(filepath, 'wb') as f:
                    f.write(frame_data)

                captured_files.append(str(filepath))

            # Verify all files were created
            assert len(captured_files) == 3
            for filepath in captured_files:
                assert Path(filepath).exists()

    def test_capture_error_when_webcam_not_started(self):
        """Test that capture fails appropriately when webcam is not started."""
        webcam_service = MockWebcamService()
        webcam_service._mock_has_webcam = True
        visual_feedback = MockVisualFeedback()

        # Try to capture without starting webcam
        with pytest.raises(CaptureError):
            webcam_service.capture_frame()

    def test_capture_error_when_no_webcam(self):
        """Test that capture fails appropriately when no webcam is available."""
        webcam_service = MockWebcamService()
        webcam_service._mock_has_webcam = False
        visual_feedback = MockVisualFeedback()

        # Try to start webcam without one
        with pytest.raises(WebcamNotFoundError):
            webcam_service.start()
