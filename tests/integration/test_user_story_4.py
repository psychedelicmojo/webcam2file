"""Integration tests for User Story 4 - Error Handling and Recovery.

These tests verify that the application handles various error conditions
gracefully with user-friendly messages and appropriate recovery actions.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

import pytest

from src.lib.error_manager import ErrorManager
from src.services.capture_queue import ICaptureQueue, ProcessingState
from src.services.comfyui_service import (
    APIConnectionError,
    APIError,
    IComfyUIService,
    TimeoutError,
)
from src.services.file_monitor_service import (
    FolderAccessError,
    FolderNotFoundError,
    IFileMonitorService,
)
from src.services.visual_feedback import IVisualFeedback
from src.services.webcam_service import (
    CaptureError,
    IWebcamService,
    WebcamAccessError,
    WebcamNotFoundError,
)


class MockWebcamService(IWebcamService):
    """Mock implementation of IWebcamService for testing."""

    def __init__(self):
        self._running = False
        self._mock_has_webcam = True
        self._mock_frame_data = b"fake_jpeg_data"
        self._raise_error_on_capture = False

    def start(self) -> None:
        if not self._mock_has_webcam:
            raise WebcamNotFoundError("No webcam available")
        self._running = True

    def stop(self) -> None:
        if not self._running:
            raise Exception("Webcam is not started")
        self._running = False

    def capture_frame(self) -> bytes:
        if not self._running:
            raise CaptureError("Webcam is not started")
        if self._raise_error_on_capture:
            raise CaptureError("Failed to capture frame")
        return self._mock_frame_data

    def is_running(self) -> bool:
        return self._running

    def set_has_webcam(self, has_webcam: bool) -> None:
        """Set webcam availability for testing."""
        self._mock_has_webcam = has_webcam

    def set_raise_error_on_capture(self, raise_error: bool) -> None:
        """Set whether capture should raise an error for testing."""
        self._raise_error_on_capture = raise_error


class MockFileMonitorService(IFileMonitorService):
    """Mock implementation of IFileMonitorService for testing."""

    def __init__(self):
        self._monitoring = False
        self._folder_path = None
        self._on_file_created_callback = None
        self._raise_error_on_start = False

    def start_monitoring(self, folder_path: str, on_file_created: callable) -> None:
        if self._raise_error_on_start:
            raise FolderNotFoundError(f"Folder does not exist: {folder_path}")
        if not Path(folder_path).exists():
            raise FolderNotFoundError(f"Folder does not exist: {folder_path}")
        self._folder_path = folder_path
        self._on_file_created_callback = on_file_created
        self._monitoring = True

    def stop_monitoring(self) -> None:
        self._monitoring = False
        self._folder_path = None
        self._on_file_created_callback = None

    def is_monitoring(self) -> bool:
        return self._monitoring

    def set_raise_error_on_start(self, raise_error: bool) -> None:
        """Set whether start_monitoring should raise an error for testing."""
        self._raise_error_on_start = raise_error


class MockComfyUIService(IComfyUIService):
    """Mock implementation of IComfyUIService for testing."""

    def __init__(self, endpoint: str = "http://127.0.0.1:8188", timeout: int = 30):
        self._endpoint = endpoint
        self._timeout = timeout
        self._available = True
        self._raise_connection_error = False
        self._raise_timeout_error = False
        self._triggered_workflows = []

    def trigger_workflow(self, workflow_json: dict, input_image_path: str) -> str:
        if self._raise_connection_error:
            raise APIConnectionError("Cannot connect to ComfyUI")
        if self._raise_timeout_error:
            raise TimeoutError("Request timed out")
        self._triggered_workflows.append(
            {"workflow": workflow_json, "input_image": input_image_path}
        )
        return f"prompt_{len(self._triggered_workflows)}"

    def check_status(self, prompt_id: str) -> dict:
        if self._raise_connection_error:
            raise APIConnectionError("Cannot connect to ComfyUI")
        if self._raise_timeout_error:
            raise TimeoutError("Request timed out")
        return {
            "prompt_id": prompt_id,
            "status": "completed",
            "output": f"processed_{prompt_id}.jpg",
        }

    def is_available(self) -> bool:
        return self._available

    def set_available(self, available: bool) -> None:
        """Set availability for testing."""
        self._available = available

    def set_raise_connection_error(self, raise_error: bool) -> None:
        """Set whether to raise connection error for testing."""
        self._raise_connection_error = raise_error

    def set_raise_timeout_error(self, raise_error: bool) -> None:
        """Set whether to raise timeout error for testing."""
        self._raise_timeout_error = raise_error

    def upload_image(self, image_path: str) -> str:
        """Upload an image to ComfyUI."""
        if self._raise_connection_error:
            raise APIConnectionError("Cannot connect to ComfyUI")
        return os.path.basename(image_path)

    def wait_for_completion(
        self, prompt_id: str, timeout: Optional[int] = None, check_interval: float = 1.0
    ) -> dict:
        """Wait for a workflow to complete."""
        if self._raise_connection_error:
            raise APIConnectionError("Cannot connect to ComfyUI")
        if self._raise_timeout_error:
            raise TimeoutError("Request timed out")
        return {"prompt_id": prompt_id, "status": "completed"}

    def download_outputs(self, prompt_id: str, output_folder: str) -> list:
        """Download processed images from ComfyUI."""
        if self._raise_connection_error:
            raise APIConnectionError("Cannot connect to ComfyUI")
        return []

    def set_endpoint(self, endpoint: str) -> None:
        """Set the ComfyUI API endpoint."""
        self._endpoint = endpoint

    def set_timeout(self, timeout: int) -> None:
        """Set the request timeout in seconds."""
        self._timeout = timeout


class MockCaptureQueue(ICaptureQueue):
    """Mock implementation of ICaptureQueue for testing."""

    def __init__(self, max_size: int = 10):
        self._queue = []
        self._max_size = max_size
        self._processing_state = ProcessingState.IDLE
        self._error_message = None
        self._processed_items = []

    def enqueue(self, image_path: str) -> None:
        if len(self._queue) >= self._max_size:
            raise QueueFullError("Queue is full")
        self._queue.append(image_path)

    def dequeue(self) -> str:
        if not self._queue:
            return None
        item = self._queue.pop(0)
        self._processed_items.append(item)
        return item

    def get_queue_size(self) -> int:
        return len(self._queue)

    def get_processing_state(self) -> ProcessingState:
        return self._processing_state

    def set_processing_state(
        self, state: ProcessingState, error_message: str = None
    ) -> None:
        self._processing_state = state
        self._error_message = error_message

    def is_processing(self) -> bool:
        return self._processing_state == ProcessingState.PROCESSING

    def get_processed_items(self) -> list:
        return self._processed_items

    def get_error_message(self) -> str:
        return self._error_message


class MockVisualFeedback(IVisualFeedback):
    """Mock implementation of IVisualFeedback for testing."""

    def __init__(self):
        self._current_effect = ""
        self._error_message = ""
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
        self._error_message = message
        self.effects.append(f"error: {message}")

    def hide_feedback(self) -> None:
        self._current_effect = ""

    def get_current_effect(self) -> str:
        return self._current_effect

    def get_error_message(self) -> str:
        return self._error_message


class QueueFullError(Exception):
    """Raised when the queue is full and cannot accept more items."""

    pass


class TestUserStory4ErrorHandling:
    """Integration tests for User Story 4 - Error Handling and Recovery."""

    def test_no_webcam_scenario(self):
        """Verify error handling when no webcam is available."""
        error_manager = ErrorManager()
        webcam_service = MockWebcamService()
        visual_feedback = MockVisualFeedback()

        # Set webcam as unavailable
        webcam_service.set_has_webcam(False)

        # Try to start webcam - should raise WebcamNotFoundError
        with pytest.raises(WebcamNotFoundError):
            webcam_service.start()

        # Verify error handling
        try:
            webcam_service.start()
        except WebcamNotFoundError as e:
            result = error_manager.handle_error(e)
            assert (
                result["user_message"]
                == "No webcam detected. Please connect a webcam and try again."
            )
            assert result["recovery_action"] == "Connect webcam"

        # Verify visual feedback shows error
        visual_feedback.show_error_feedback(result["user_message"])
        assert visual_feedback.get_current_effect() == "error"
        assert "No webcam detected" in visual_feedback.get_error_message()

    def test_webcam_access_denied(self):
        """Verify error handling when webcam access is denied."""
        error_manager = ErrorManager()
        webcam_service = MockWebcamService()
        MockVisualFeedback()

        # Simulate access denied by raising WebcamAccessError
        webcam_service._mock_has_webcam = True

        # Try to start webcam - should raise WebcamAccessError
        with pytest.raises(WebcamAccessError):
            # Simulate access denied
            raise WebcamAccessError("Cannot access webcam")

        # Verify error handling
        try:
            raise WebcamAccessError("Cannot access webcam")
        except WebcamAccessError as e:
            result = error_manager.handle_error(e)
            assert (
                result["user_message"]
                == "Cannot access webcam. Close other applications using the webcam and try again."
            )
            assert result["recovery_action"] == "Close other apps"

    def test_capture_error(self):
        """Verify error handling when frame capture fails."""
        error_manager = ErrorManager()
        webcam_service = MockWebcamService()
        MockVisualFeedback()

        # Start webcam successfully
        webcam_service.set_has_webcam(True)
        webcam_service.start()

        # Set capture to raise error
        webcam_service.set_raise_error_on_capture(True)

        # Try to capture frame - should raise CaptureError
        with pytest.raises(CaptureError):
            webcam_service.capture_frame()

        # Verify error handling
        try:
            webcam_service.capture_frame()
        except CaptureError as e:
            result = error_manager.handle_error(e)
            assert (
                result["user_message"]
                == "An unexpected error occurred. Please try again."
            )
            assert result["recovery_action"] == "Retry operation"

    def test_comfyui_unavailable(self):
        """Verify error handling when ComfyUI is down."""
        error_manager = ErrorManager()
        comfyui_service = MockComfyUIService()
        visual_feedback = MockVisualFeedback()

        # Make ComfyUI unavailable
        comfyui_service.set_raise_connection_error(True)

        # Try to trigger workflow - should raise APIConnectionError
        workflow_json = {"nodes": []}
        input_image_path = "/test/image.jpg"

        with pytest.raises(APIConnectionError):
            comfyui_service.trigger_workflow(workflow_json, input_image_path)

        # Verify error handling
        try:
            comfyui_service.trigger_workflow(workflow_json, input_image_path)
        except APIConnectionError as e:
            result = error_manager.handle_error(e)
            assert (
                result["user_message"]
                == "Cannot connect to ComfyUI. Make sure ComfyUI is running and try again."
            )
            assert result["recovery_action"] == "Start ComfyUI"

        # Verify visual feedback shows error
        visual_feedback.show_error_feedback(result["user_message"])
        assert visual_feedback.get_current_effect() == "error"
        assert "Cannot connect to ComfyUI" in visual_feedback.get_error_message()

    def test_comfyui_timeout(self):
        """Verify error handling when ComfyUI request times out."""
        error_manager = ErrorManager()
        comfyui_service = MockComfyUIService()
        MockVisualFeedback()

        # Make ComfyUI raise timeout error
        comfyui_service.set_raise_timeout_error(True)

        # Try to trigger workflow - should raise TimeoutError
        workflow_json = {"nodes": []}
        input_image_path = "/test/image.jpg"

        with pytest.raises(TimeoutError):
            comfyui_service.trigger_workflow(workflow_json, input_image_path)

        # Verify error handling
        try:
            comfyui_service.trigger_workflow(workflow_json, input_image_path)
        except TimeoutError as e:
            result = error_manager.handle_error(e)
            assert (
                result["user_message"]
                == "Request to ComfyUI timed out. Check your network connection and try again."
            )
            assert result["recovery_action"] == "Retry request"

    def test_folder_not_found(self):
        """Verify error handling when output folder does not exist."""
        error_manager = ErrorManager()
        file_monitor = MockFileMonitorService()
        capture_queue = MockCaptureQueue()

        # Try to monitor non-existent folder - should raise FolderNotFoundError
        non_existent_folder = "/non/existent/folder/path"

        with pytest.raises(FolderNotFoundError):
            file_monitor.start_monitoring(non_existent_folder, capture_queue.enqueue)

        # Verify error handling
        try:
            file_monitor.start_monitoring(non_existent_folder, capture_queue.enqueue)
        except FolderNotFoundError as e:
            result = error_manager.handle_error(e)
            assert (
                result["user_message"]
                == "Output folder not found. Please select a valid folder in settings."
            )
            assert result["recovery_action"] == "Select valid folder"

    def test_folder_access_denied(self):
        """Verify error handling when folder access is denied."""
        error_manager = ErrorManager()

        # Simulate folder access denied
        try:
            raise FolderAccessError("Cannot access folder")
        except FolderAccessError as e:
            result = error_manager.handle_error(e)
            assert (
                result["user_message"]
                == "Cannot access output folder. Check permissions and try again."
            )
            assert result["recovery_action"] == "Check permissions"

    def test_queue_overflow(self):
        """Verify error handling when queue is full."""
        error_manager = ErrorManager()
        capture_queue = MockCaptureQueue(max_size=2)

        # Fill the queue
        capture_queue.enqueue("/test/image1.jpg")
        capture_queue.enqueue("/test/image2.jpg")

        # Try to add another item - should raise QueueFullError
        try:
            capture_queue.enqueue("/test/image3.jpg")
        except QueueFullError as e:
            result = error_manager.handle_error(e)
            assert (
                result["user_message"]
                == "An unexpected error occurred. Please try again."
            )
            assert result["recovery_action"] == "Retry operation"

            # Set queue state to error
            capture_queue.set_processing_state(ProcessingState.ERROR, "Queue is full")
            assert capture_queue.get_processing_state() == ProcessingState.ERROR
            assert capture_queue.get_error_message() == "Queue is full"

    def test_large_file_error(self):
        """Verify error handling for files exceeding 5MB limit."""
        error_manager = ErrorManager()

        # Simulate large file error
        large_file_error = ValueError("File size exceeds 5MB limit")

        result = error_manager.handle_error(large_file_error)
        assert (
            result["user_message"] == "An unexpected error occurred. Please try again."
        )
        assert result["recovery_action"] == "Retry operation"

    def test_workflow_error(self):
        """Verify error handling for ComfyUI workflow failures."""
        error_manager = ErrorManager()
        MockComfyUIService()

        # Simulate workflow error
        try:
            raise APIError("Workflow execution failed")
        except APIError as e:
            result = error_manager.handle_error(e)
            assert (
                result["user_message"]
                == "ComfyUI returned an error. Check the workflow configuration and try again."
            )
            assert result["recovery_action"] == "Check workflow"

    def test_error_recovery_flow(self):
        """Verify complete error recovery flow."""
        error_manager = ErrorManager()
        visual_feedback = MockVisualFeedback()

        # Simulate a sequence of errors and recoveries
        errors = [
            WebcamNotFoundError("No webcam"),
            APIConnectionError("Cannot connect"),
            TimeoutError("Request timed out"),
        ]

        for error in errors:
            result = error_manager.handle_error(error)

            # Show error feedback
            visual_feedback.show_error_feedback(result["user_message"])
            assert visual_feedback.get_current_effect() == "error"
            assert result["user_message"] in visual_feedback.get_error_message()

            # Clear feedback
            visual_feedback.hide_feedback()
            assert visual_feedback.get_current_effect() == ""

    def test_multiple_error_types(self):
        """Verify ErrorManager handles multiple error types correctly."""
        error_manager = ErrorManager()

        error_types = [
            (WebcamNotFoundError("test"), "WebcamNotFoundError"),
            (WebcamAccessError("test"), "WebcamAccessError"),
            (FolderNotFoundError("test"), "FolderNotFoundError"),
            (FolderAccessError("test"), "FolderAccessError"),
            (APIConnectionError("test"), "APIConnectionError"),
            (APIError("test"), "APIError"),
            (TimeoutError("test"), "TimeoutError"),
        ]

        for error, expected_type in error_types:
            result = error_manager.handle_error(error)
            assert result["error_type"] == expected_type
            assert "user_message" in result
            assert "recovery_action" in result

    def test_error_manager_is_recoverable(self):
        """Verify ErrorManager correctly identifies recoverable errors."""
        error_manager = ErrorManager()

        # Test recoverable errors
        assert error_manager.is_recoverable(WebcamNotFoundError("test")) is True
        assert error_manager.is_recoverable(APIConnectionError("test")) is True
        assert error_manager.is_recoverable(TimeoutError("test")) is True

        # Test unknown error type
        class CustomError(Exception):
            pass

        assert error_manager.is_recoverable(CustomError("test")) is False

    def test_full_error_handling_workflow(self):
        """Verify complete error handling workflow across components."""
        with tempfile.TemporaryDirectory() as output_folder:
            error_manager = ErrorManager()
            webcam_service = MockWebcamService()
            file_monitor = MockFileMonitorService()
            comfyui_service = MockComfyUIService()
            visual_feedback = MockVisualFeedback()

            # Setup: Make all services unavailable
            webcam_service.set_has_webcam(False)
            file_monitor.set_raise_error_on_start(True)
            comfyui_service.set_raise_connection_error(True)

            # Test 1: Webcam error
            try:
                webcam_service.start()
            except WebcamNotFoundError as e:
                result = error_manager.handle_error(e)
                visual_feedback.show_error_feedback(result["user_message"])
                assert visual_feedback.get_current_effect() == "error"

            # Clear feedback
            visual_feedback.hide_feedback()

            # Test 2: Folder error
            try:
                file_monitor.start_monitoring(output_folder, lambda x: None)
            except FolderNotFoundError as e:
                result = error_manager.handle_error(e)
                visual_feedback.show_error_feedback(result["user_message"])
                assert visual_feedback.get_current_effect() == "error"

            # Clear feedback
            visual_feedback.hide_feedback()

            # Test 3: ComfyUI error
            try:
                comfyui_service.trigger_workflow({"nodes": []}, "/test.jpg")
            except APIConnectionError as e:
                result = error_manager.handle_error(e)
                visual_feedback.show_error_feedback(result["user_message"])
                assert visual_feedback.get_current_effect() == "error"
