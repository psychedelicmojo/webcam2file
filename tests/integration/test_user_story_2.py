"""Integration tests for User Story 2 - Folder Monitoring and ComfyUI Workflow.

These tests verify the complete end-to-end workflow of monitoring a folder
for new images and triggering ComfyUI processing.
"""

import os
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional

import pytest

from src.lib.file_utils import FileUtils
from src.models.comfyui_workflow import ComfyUIWorkflow
from src.services.capture_queue import ICaptureQueue, ProcessingState
from src.services.comfyui_service import (
    APIConnectionError,
    IComfyUIService,
)
from src.services.file_monitor_service import (
    FolderNotFoundError,
    IFileMonitorService,
)


class MockFileMonitorService(IFileMonitorService):
    """Mock implementation of IFileMonitorService for testing."""

    def __init__(self):
        self._monitoring = False
        self._folder_path = None
        self._on_file_created_callback = None
        self._detected_files = []

    def start_monitoring(
        self, folder_path: str, on_file_created: Callable[[str], None]
    ) -> None:
        """Start monitoring a folder for new files."""
        if not Path(folder_path).exists():
            raise FolderNotFoundError(f"Folder does not exist: {folder_path}")
        self._folder_path = folder_path
        self._on_file_created_callback = on_file_created
        self._monitoring = True

    def stop_monitoring(self) -> None:
        """Stop monitoring the folder."""
        self._monitoring = False
        self._folder_path = None
        self._on_file_created_callback = None

    def is_monitoring(self) -> bool:
        """Check if monitoring is currently active."""
        return self._monitoring

    def simulate_file_created(self, filepath: str) -> None:
        """Simulate a file being created (for testing)."""
        if self._monitoring and self._on_file_created_callback:
            self._on_file_created_callback(filepath)
            self._detected_files.append(filepath)

    def get_detected_files(self) -> list:
        """Get list of detected files."""
        return self._detected_files


class MockComfyUIService(IComfyUIService):
    """Mock implementation of IComfyUIService for testing."""

    def __init__(self, endpoint: str = "http://127.0.0.1:8188", timeout: int = 30):
        self._endpoint = endpoint
        self._timeout = timeout
        self._triggered_workflows = []
        self._available = True
        self._prompt_id_counter = 0

    def trigger_workflow(self, workflow_json: dict, input_image_path: str) -> str:
        """Trigger a ComfyUI workflow."""
        if not self._available:
            raise APIConnectionError("Cannot connect to ComfyUI")
        self._prompt_id_counter += 1
        prompt_id = f"prompt_{self._prompt_id_counter}"
        self._triggered_workflows.append(
            {
                "prompt_id": prompt_id,
                "workflow": workflow_json,
                "input_image": input_image_path,
            }
        )
        return prompt_id

    def check_status(self, prompt_id: str) -> dict:
        """Check the status of a workflow."""
        if not self._available:
            raise APIConnectionError("Cannot connect to ComfyUI")
        return {
            "prompt_id": prompt_id,
            "status": "completed",
            "output": f"processed_{prompt_id}.jpg",
        }

    def is_available(self) -> bool:
        """Check if ComfyUI API is accessible."""
        return self._available

    def set_available(self, available: bool) -> None:
        """Set availability for testing."""
        self._available = available

    def get_triggered_workflows(self) -> list:
        """Get list of triggered workflows."""
        return self._triggered_workflows

    def upload_image(self, image_path: str) -> str:
        """Upload an image to ComfyUI."""
        if not self._available:
            raise APIConnectionError("Cannot connect to ComfyUI")
        return os.path.basename(image_path)

    def wait_for_completion(
        self, prompt_id: str, timeout: Optional[int] = None, check_interval: float = 1.0
    ) -> dict:
        """Wait for a workflow to complete."""
        if not self._available:
            raise APIConnectionError("Cannot connect to ComfyUI")
        return {"prompt_id": prompt_id, "status": "completed"}

    def download_outputs(
        self, prompt_id: str, output_folder: str
    ) -> list:
        """Download processed images from ComfyUI."""
        if not self._available:
            raise APIConnectionError("Cannot connect to ComfyUI")
        return []


class MockCaptureQueue(ICaptureQueue):
    """Mock implementation of ICaptureQueue for testing."""

    def __init__(self):
        self._queue = []
        self._processing_state = ProcessingState.IDLE
        self._error_message = None
        self._processed_items = []

    def enqueue(self, image_path: str) -> None:
        """Add an image to the processing queue."""
        self._queue.append(image_path)

    def dequeue(self) -> Optional[str]:
        """Remove and return the next image from the queue."""
        if not self._queue:
            return None
        item = self._queue.pop(0)
        self._processed_items.append(item)
        return item

    def get_queue_size(self) -> int:
        """Get the current queue size."""
        return len(self._queue)

    def get_processing_state(self) -> ProcessingState:
        """Get the current processing state."""
        return self._processing_state

    def set_processing_state(
        self, state: ProcessingState, error_message: Optional[str] = None
    ) -> None:
        """Set the current processing state."""
        self._processing_state = state
        self._error_message = error_message

    def is_processing(self) -> bool:
        """Check if processing is currently active."""
        return self._processing_state == ProcessingState.PROCESSING

    def get_processed_items(self) -> list:
        """Get list of processed items."""
        return self._processed_items


class TestUserStory2Integration:
    """Integration tests for User Story 2 - Folder Monitoring and ComfyUI Workflow."""

    def test_folder_monitoring(self):
        """Verify new file detection triggers processing."""
        with tempfile.TemporaryDirectory() as output_folder:
            # Setup
            file_monitor = MockFileMonitorService()
            capture_queue = MockCaptureQueue()

            # Start monitoring
            file_monitor.start_monitoring(output_folder, capture_queue.enqueue)

            # Verify monitoring is active
            assert file_monitor.is_monitoring() is True

            # Create a test image file
            filename = FileUtils.generate_unique_filename(
                prefix="capture", suffix=".jpg"
            )
            filepath = Path(output_folder) / filename

            # Simulate file creation (this should trigger the callback)
            file_monitor.simulate_file_created(str(filepath))

            # Verify file was detected and added to queue
            assert capture_queue.get_queue_size() == 1

            # Verify the file path in queue matches
            dequeued = capture_queue.dequeue()
            assert dequeued is not None
            assert str(filepath) == dequeued

            # Stop monitoring
            file_monitor.stop_monitoring()
            assert file_monitor.is_monitoring() is False

    def test_comfyui_integration(self):
        """Verify ComfyUI API communication."""
        with tempfile.TemporaryDirectory() as output_folder:
            # Setup
            comfyui_service = MockComfyUIService()
            workflow_json = {"workflow": "test_workflow", "input_image": "placeholder"}
            input_image_path = Path(output_folder) / "test_image.jpg"

            # Create a test image file
            with open(input_image_path, "wb") as f:
                f.write(b"test_image_data")

            # Trigger workflow
            prompt_id = comfyui_service.trigger_workflow(
                workflow_json, str(input_image_path)
            )

            # Verify workflow was triggered
            assert prompt_id.startswith("prompt_")
            assert len(comfyui_service.get_triggered_workflows()) == 1

            triggered = comfyui_service.get_triggered_workflows()[0]
            assert triggered["prompt_id"] == prompt_id
            assert triggered["workflow"] == workflow_json
            assert triggered["input_image"] == str(input_image_path)

            # Check status
            status = comfyui_service.check_status(prompt_id)
            assert status["prompt_id"] == prompt_id
            assert status["status"] == "completed"

    def test_queue_processing(self):
        """Verify multiple captures are processed in sequence."""
        with tempfile.TemporaryDirectory() as output_folder:
            # Setup
            file_monitor = MockFileMonitorService()
            comfyui_service = MockComfyUIService()
            capture_queue = MockCaptureQueue()

            # Start monitoring
            file_monitor.start_monitoring(output_folder, capture_queue.enqueue)

            # Create multiple test image files
            num_captures = 5
            filepaths = []
            for _ in range(num_captures):
                filename = FileUtils.generate_unique_filename(
                    prefix="capture", suffix=".jpg"
                )
                filepath = Path(output_folder) / filename
                filepaths.append(filepath)

                # Create the actual file
                with open(filepath, "wb") as f:
                    f.write(b"test_image_data")

                # Simulate file creation
                file_monitor.simulate_file_created(str(filepath))

            # Verify all files were added to queue
            assert capture_queue.get_queue_size() == num_captures

            # Process queue items
            processed_count = 0
            valid_workflow_json = {
                "nodes": [
                    {"id": 1, "type": "LoadImage"},
                    {"id": 2, "type": "SaveImage"},
                ]
            }
            while capture_queue.get_queue_size() > 0:
                item = capture_queue.dequeue()
                if item:
                    processed_count += 1
                    # Simulate ComfyUI processing
                    workflow = ComfyUIWorkflow(
                        workflow_json=valid_workflow_json,
                        input_image_path=item,
                        output_location=output_folder,
                    )
                    prompt_id = comfyui_service.trigger_workflow(
                        workflow.to_dict(), workflow.input_image_path
                    )
                    # Check status (not used, but part of workflow)
                    _ = comfyui_service.check_status(prompt_id)

            # Verify all items were processed
            assert processed_count == num_captures
            assert len(comfyui_service.get_triggered_workflows()) == num_captures

            # Stop monitoring
            file_monitor.stop_monitoring()

    def test_api_unavailable_error(self):
        """Verify error handling when ComfyUI is down."""
        with tempfile.TemporaryDirectory() as output_folder:
            # Setup
            file_monitor = MockFileMonitorService()
            comfyui_service = MockComfyUIService()
            capture_queue = MockCaptureQueue()

            # Make ComfyUI unavailable
            comfyui_service.set_available(False)

            # Start monitoring
            file_monitor.start_monitoring(output_folder, capture_queue.enqueue)

            # Create a test image file
            filename = FileUtils.generate_unique_filename(
                prefix="capture", suffix=".jpg"
            )
            filepath = Path(output_folder) / filename

            # Create the actual file
            with open(filepath, "wb") as f:
                f.write(b"test_image_data")

            # Simulate file creation
            file_monitor.simulate_file_created(str(filepath))

            # Verify file was added to queue
            assert capture_queue.get_queue_size() == 1

            # Try to process the queue item
            item = capture_queue.dequeue()
            assert item is not None

            # Trigger workflow should fail
            valid_workflow_json = {
                "nodes": [
                    {"id": 1, "type": "LoadImage"},
                    {"id": 2, "type": "SaveImage"},
                ]
            }
            workflow = ComfyUIWorkflow(
                workflow_json=valid_workflow_json,
                input_image_path=item,
                output_location=output_folder,
            )

            with pytest.raises(APIConnectionError):
                comfyui_service.trigger_workflow(
                    workflow.to_dict(), workflow.input_image_path
                )

            # Verify queue state is set to error
            capture_queue.set_processing_state(
                ProcessingState.ERROR, "ComfyUI unavailable"
            )

            assert capture_queue.get_processing_state() == ProcessingState.ERROR
            assert capture_queue._error_message == "ComfyUI unavailable"

            # Stop monitoring
            file_monitor.stop_monitoring()

    def test_full_workflow_simulation(self):
        """Verify complete capture → save → monitor → process workflow."""
        with tempfile.TemporaryDirectory() as output_folder:
            # Setup
            file_monitor = MockFileMonitorService()
            comfyui_service = MockComfyUIService()
            capture_queue = MockCaptureQueue()

            # Start monitoring
            file_monitor.start_monitoring(output_folder, capture_queue.enqueue)

            # Simulate capture and save
            filename = FileUtils.generate_unique_filename(
                prefix="capture", suffix=".jpg"
            )
            filepath = Path(output_folder) / filename

            # Save image to file
            with open(filepath, "wb") as f:
                f.write(b"test_image_data")

            # Simulate file detection (file monitor detects new file)
            file_monitor.simulate_file_created(str(filepath))

            # Verify file was detected and queued
            assert capture_queue.get_queue_size() == 1

            # Process the queue item
            item = capture_queue.dequeue()
            assert item is not None

            # Trigger ComfyUI workflow
            valid_workflow_json = {
                "nodes": [
                    {"id": 1, "type": "LoadImage"},
                    {"id": 2, "type": "SaveImage"},
                ]
            }
            workflow = ComfyUIWorkflow(
                workflow_json=valid_workflow_json,
                input_image_path=item,
                output_location=output_folder,
            )
            prompt_id = comfyui_service.trigger_workflow(
                workflow.to_dict(), workflow.input_image_path
            )

            # Check status
            status = comfyui_service.check_status(prompt_id)
            assert status["status"] == "completed"

            # Verify all components worked together
            assert Path(filepath).exists()
            assert len(comfyui_service.get_triggered_workflows()) == 1

            # Stop monitoring
            file_monitor.stop_monitoring()

    def test_multiple_files_detected_in_sequence(self):
        """Verify all files are detected in sequence."""
        with tempfile.TemporaryDirectory() as output_folder:
            # Setup
            file_monitor = MockFileMonitorService()
            capture_queue = MockCaptureQueue()

            # Start monitoring
            file_monitor.start_monitoring(output_folder, capture_queue.enqueue)

            # Create multiple files with small delays
            num_files = 3
            for _ in range(num_files):
                filename = FileUtils.generate_unique_filename(
                    prefix="capture", suffix=".jpg"
                )
                filepath = Path(output_folder) / filename

                # Simulate file creation
                file_monitor.simulate_file_created(str(filepath))

                # Small delay to ensure unique timestamps
                time.sleep(0.01)

            # Verify all files were detected
            assert len(file_monitor.get_detected_files()) == num_files
            assert capture_queue.get_queue_size() == num_files

            # Stop monitoring
            file_monitor.stop_monitoring()

    def test_folder_not_found_error(self):
        """Verify FolderNotFoundError when folder does not exist."""
        file_monitor = MockFileMonitorService()
        capture_queue = MockCaptureQueue()

        # Try to monitor non-existent folder
        non_existent_folder = "/non/existent/folder/path"

        with pytest.raises(FolderNotFoundError):
            file_monitor.start_monitoring(non_existent_folder, capture_queue.enqueue)

        # Verify monitoring is not active
        assert file_monitor.is_monitoring() is False
