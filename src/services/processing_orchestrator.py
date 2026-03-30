"""Orchestrator service for coordinating file monitoring, queue management, and ComfyUI processing."""

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from src.lib.error_manager import ErrorManager
from src.models.application_settings import ApplicationSettings
from src.models.image_capture import ImageCapture
from src.models.processing_status import ProcessingStatus
from src.services.capture_queue import ProcessingState
from src.services.capture_queue_impl import CaptureQueue, QueueFullError
from src.services.comfyui_service import APIConnectionError, APIError, TimeoutError
from src.services.comfyui_service_impl import ComfyUIService
from src.services.file_monitor_impl import FileMonitorServiceImpl
from src.services.file_monitor_service import FolderAccessError, FolderNotFoundError
from src.services.visual_feedback import IVisualFeedback

logger = logging.getLogger(__name__)


class ProcessingOrchestrator:
    """Orchestrator service for coordinating file monitoring, queue management, and ComfyUI processing.

    This service coordinates the end-to-end workflow:
    1. Monitors output folder for new JPEG files
    2. Enqueues captured images for processing
    3. Processes images through ComfyUI API
    4. Updates processing status and provides visual feedback
    """

    # Retry configuration for transient failures
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 2

    def __init__(self, settings: ApplicationSettings, visual_feedback: IVisualFeedback):
        """Initialize the processing orchestrator.

        Args:
            settings: Application settings containing ComfyUI endpoint and workflow config
            visual_feedback: Service for visual feedback display
        """
        self._settings = settings
        self._visual_feedback = visual_feedback
        self._error_manager = ErrorManager()

        # Initialize services
        self._capture_queue = CaptureQueue(max_size=100)
        self._comfyui_service = ComfyUIService(
            endpoint=settings.comfyui_endpoint, timeout=settings.api_timeout
        )

        # File monitor callback
        self._file_monitor = FileMonitorServiceImpl(file_extensions=[".jpg", ".jpeg"])

        # State management
        self._running = False
        self._monitoring = False
        self._processing_thread: Optional[threading.Thread] = None
        self._status = ProcessingStatus(
            state="idle", current_image="", error_message="", queue_size=0
        )

        # Callbacks
        self._on_status_change: Optional[Callable[[ProcessingStatus], None]] = None
        self._on_processing_complete: Optional[Callable[[ImageCapture], None]] = None
        self._on_processing_error: Optional[Callable[[ImageCapture, str], None]] = None

    def start(self) -> None:
        """Start the processing orchestrator.

        Begins file monitoring and starts the processing worker thread.
        """
        if self._running:
            return

        self._running = True

        # Start file monitoring
        try:
            self._file_monitor.start_monitoring(
                folder_path=self._settings.output_folder,
                on_file_created=self._on_file_created,
            )
            self._monitoring = True
        except (FolderNotFoundError, FolderAccessError) as e:
            error_info = self._error_manager.handle_error(
                e,
                "Cannot access output folder. Please select a valid folder in settings.",
            )
            self._status = ProcessingStatus(
                state="error",
                current_image="",
                error_message=error_info["user_message"],
                queue_size=0,
            )
            self._visual_feedback.show_error_feedback(error_info["user_message"])
            logger.error(f"Failed to start orchestrator: {error_info['user_message']}")
            raise

        # Start processing worker thread
        self._processing_thread = threading.Thread(
            target=self._process_queue, daemon=True
        )
        self._processing_thread.start()
        logger.info("Processing orchestrator started")

    def stop(self) -> None:
        """Stop the processing orchestrator.

        Shuts down file monitoring and processing worker thread.
        """
        self._running = False

        # Stop file monitoring
        if self._monitoring:
            self._file_monitor.stop_monitoring()
            self._monitoring = False

        # Wait for processing thread to finish
        if self._processing_thread is not None:
            self._processing_thread.join(timeout=5.0)
            self._processing_thread = None
        logger.info("Processing orchestrator stopped")

    def _on_file_created(self, filepath: str) -> None:
        """Callback for when a new file is created.

        Args:
            filepath: Path to the newly created file.
        """
        if not self._running:
            return

        # Wait for file to be fully written
        from src.lib.file_utils import FileUtils

        if not FileUtils.wait_for_file_ready(filepath, timeout=5.0):
            self._visual_feedback.show_error_feedback(
                f"Could not access file: {filepath}"
            )
            logger.warning(f"File not ready for processing: {filepath}")
            return

        # Get file size
        try:
            filesize = Path(filepath).stat().st_size
        except OSError as e:
            self._visual_feedback.show_error_feedback(
                f"Could not read file size: {str(e)}"
            )
            logger.error(f"Failed to read file size for {filepath}: {e}")
            return

        # Create ImageCapture object
        filename = Path(filepath).stem
        timestamp = filename.replace("capture_", "")

        ImageCapture(
            timestamp=timestamp,
            filepath=filepath,
            filesize=filesize,
            output_folder=self._settings.output_folder,
            status="pending",
        )

        # Enqueue for processing
        try:
            self._capture_queue.enqueue(filepath)
            self._update_status()
            self._visual_feedback.show_processing_feedback()
            logger.info(f"Image enqueued for processing: {filepath}")
        except QueueFullError:
            self._visual_feedback.show_error_feedback(
                "Processing queue is full. Image not added."
            )
            logger.warning(f"Queue full, could not enqueue: {filepath}")

    def _process_queue(self) -> None:
        """Worker thread that processes items from the queue."""
        while self._running:
            # Get next item from queue
            filepath = self._capture_queue.dequeue()

            if filepath is None:
                # Queue is empty, wait before checking again
                time.sleep(0.5)
                continue

            # Process the image with retry logic
            self._process_image_with_retry(filepath)

            # Update status
            self._update_status()

    def _process_image_with_retry(self, filepath: str) -> None:
        """Process a single image through ComfyUI with retry logic.

        Args:
            filepath: Path to the image to process.
        """
        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                self._process_image(filepath)
                return  # Success, exit retry loop
            except (APIConnectionError, TimeoutError) as e:
                last_error = str(e)
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(
                        f"Transient error processing {filepath} (attempt {attempt + 1}/{self.MAX_RETRIES}): {last_error}"
                    )
                    time.sleep(self.RETRY_DELAY_SECONDS)
                else:
                    logger.error(
                        f"Failed to process {filepath} after {self.MAX_RETRIES} attempts: {last_error}"
                    )
                    self._handle_processing_error(filepath, last_error)
            except APIError as e:
                # API errors are not retryable, handle immediately
                last_error = str(e)
                logger.error(
                    f"Non-retryable API error processing {filepath}: {last_error}"
                )
                self._handle_processing_error(filepath, last_error)
                return
            except Exception as e:
                # Unexpected errors are not retryable
                last_error = f"Unexpected error: {str(e)}"
                logger.error(f"Unexpected error processing {filepath}: {last_error}")
                self._handle_processing_error(filepath, last_error)
                return

    def _process_image(self, filepath: str) -> None:
        """Process a single image through ComfyUI.

        Args:
            filepath: Path to the image to process.

        Raises:
            APIConnectionError: If connection to ComfyUI fails
            APIError: If ComfyUI returns an error response
            TimeoutError: If request times out
        """
        # Update status to processing
        self._capture_queue.set_processing_state(ProcessingState.PROCESSING)
        self._capture_queue.set_current_image(filepath)
        self._update_status()

        # Load workflow JSON from file
        workflow_path = Path(self._settings.workflow_json_path)
        try:
            with open(workflow_path, "r") as f:
                workflow_json = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            error_msg = f"Failed to load workflow JSON: {str(e)}"
            logger.error(f"Workflow loading error for {filepath}: {error_msg}")
            raise APIError(error_msg) from e

        # Upload image to ComfyUI
        try:
            uploaded_filename = self._comfyui_service.upload_image(filepath)
            logger.info(f"Image uploaded to ComfyUI as: {uploaded_filename}")
        except (APIConnectionError, APIError, TimeoutError) as e:
            logger.error(f"Failed to upload image for {filepath}: {e}")
            raise

        # Dynamically update workflow JSON with uploaded filename
        try:
            updated_workflow = self._update_workflow_with_image(
                workflow_json, uploaded_filename
            )
        except APIError as e:
            logger.error(f"Failed to update workflow for {filepath}: {e}")
            raise

        # Trigger workflow
        try:
            prompt_id = self._comfyui_service.trigger_workflow(
                workflow_json=updated_workflow, input_image_path=filepath
            )
            logger.info(f"Workflow triggered for {filepath}, prompt_id: {prompt_id}")
        except (APIConnectionError, APIError, TimeoutError) as e:
            logger.error(f"Failed to trigger workflow for {filepath}: {e}")
            raise

        # Wait for completion
        try:
            self._comfyui_service.wait_for_completion(prompt_id)
            logger.info(f"Workflow completed for {filepath}")
        except (APIConnectionError, APIError, TimeoutError) as e:
            logger.error(f"Failed to wait for workflow completion for {filepath}: {e}")
            raise

        # Download output images
        try:
            downloaded_files = self._comfyui_service.download_outputs(
                prompt_id, self._settings.output_folder
            )
            logger.info(f"Downloaded {len(downloaded_files)} output image(s)")
        except (APIConnectionError, APIError, TimeoutError) as e:
            logger.error(f"Failed to download outputs for {filepath}: {e}")
            raise

        # Update status to completed
        self._capture_queue.set_processing_state(ProcessingState.COMPLETED)
        self._capture_queue.set_current_image("")

        # Update image capture status
        image_capture = ImageCapture(
            timestamp=Path(filepath).stem.replace("capture_", ""),
            filepath=filepath,
            filesize=Path(filepath).stat().st_size,
            output_folder=self._settings.output_folder,
            status="completed",
        )

        if self._on_processing_complete:
            self._on_processing_complete(image_capture)

        self._visual_feedback.show_completion_feedback()
        logger.info(f"Processing completed successfully: {filepath}")

    def _update_workflow_with_image(
        self, workflow_json: Dict[str, Any], uploaded_filename: str
    ) -> Dict[str, Any]:
        """Dynamically update the workflow JSON with the uploaded image filename.

        This method traverses the workflow nodes to find LoadImage nodes and updates
        their inputs.image value with the uploaded filename.

        Args:
            workflow_json: The original workflow JSON.
            uploaded_filename: The filename returned by the upload endpoint.

        Returns:
            Dict[str, Any]: A new workflow JSON with updated image references.

        Raises:
            APIError: If no LoadImage node is found in the workflow.
        """
        import copy

        # Create a deep copy to avoid modifying the original
        updated_workflow = copy.deepcopy(workflow_json)

        # Check if nodes is a dict (ComfyUI format) or list
        nodes = updated_workflow.get("nodes", [])

        if isinstance(nodes, dict):
            # ComfyUI format: nodes is a dict with node_id as key
            for node_id, node_data in nodes.items():
                if isinstance(node_data, dict) and node_data.get("class_type") == "LoadImage":
                    # Found a LoadImage node, update its inputs.image
                    inputs = node_data.get("inputs", {})
                    if isinstance(inputs, dict):
                        inputs["image"] = uploaded_filename
                        node_data["inputs"] = inputs
                        logger.debug(f"Updated LoadImage node {node_id} with image: {uploaded_filename}")
                        return updated_workflow
        elif isinstance(nodes, list):
            # Alternative format: nodes is a list
            for node_data in nodes:
                if isinstance(node_data, dict) and node_data.get("class_type") == "LoadImage":
                    # Found a LoadImage node, update its inputs.image
                    inputs = node_data.get("inputs", {})
                    if isinstance(inputs, dict):
                        inputs["image"] = uploaded_filename
                        node_data["inputs"] = inputs
                        logger.debug(f"Updated LoadImage node with image: {uploaded_filename}")
                        return updated_workflow

        raise APIError(
            "Workflow does not contain a LoadImage node. "
            "Please ensure your ComfyUI workflow includes a LoadImage node."
        )

    def _handle_processing_error(self, filepath: str, error_message: str) -> None:
        """Handle a processing error.

        Args:
            filepath: Path to the image that failed.
            error_message: Error message describing the failure.
        """
        # Update status to error
        self._capture_queue.set_processing_state(ProcessingState.ERROR, error_message)
        self._capture_queue.set_current_image("")

        # Update image capture status
        image_capture = ImageCapture(
            timestamp=Path(filepath).stem.replace("capture_", ""),
            filepath=filepath,
            filesize=Path(filepath).stat().st_size,
            output_folder=self._settings.output_folder,
            status="error",
        )

        if self._on_processing_error:
            self._on_processing_error(image_capture, error_message)

        self._visual_feedback.show_error_feedback(error_message)
        logger.error(f"Processing failed for {filepath}: {error_message}")

    def _update_status(self) -> None:
        """Update the processing status."""
        state = self._capture_queue.get_processing_state().value
        current_image = self._capture_queue.get_current_image() or ""
        queue_size = self._capture_queue.get_queue_size()
        error_message = self._capture_queue.get_error_message() or ""

        self._status = ProcessingStatus(
            state=state,
            current_image=current_image,
            error_message=error_message,
            queue_size=queue_size,
        )

        if self._on_status_change:
            self._on_status_change(self._status)

    def is_running(self) -> bool:
        """Check if the orchestrator is running.

        Returns:
            bool: True if running, False otherwise.
        """
        return self._running

    def is_monitoring(self) -> bool:
        """Check if file monitoring is active.

        Returns:
            bool: True if monitoring, False otherwise.
        """
        return self._monitoring

    def get_status(self) -> ProcessingStatus:
        """Get the current processing status.

        Returns:
            ProcessingStatus: Current status information.
        """
        return self._status

    def set_on_status_change(
        self, callback: Callable[[ProcessingStatus], None]
    ) -> None:
        """Set callback for status changes.

        Args:
            callback: Function to call when status changes.
        """
        self._on_status_change = callback

    def set_on_processing_complete(
        self, callback: Callable[[ImageCapture], None]
    ) -> None:
        """Set callback for processing completion.

        Args:
            callback: Function to call when processing completes.
        """
        self._on_processing_complete = callback

    def set_on_processing_error(
        self, callback: Callable[[ImageCapture, str], None]
    ) -> None:
        """Set callback for processing errors.

        Args:
            callback: Function to call when processing fails.
        """
        self._on_processing_error = callback
