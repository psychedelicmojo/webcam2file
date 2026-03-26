"""Orchestrator service for coordinating file monitoring, queue management, and ComfyUI processing."""

import json
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from src.models.application_settings import ApplicationSettings
from src.models.comfyui_workflow import ComfyUIWorkflow
from src.models.image_capture import ImageCapture
from src.models.processing_status import ProcessingStatus
from src.services.capture_queue import ProcessingState
from src.services.capture_queue_impl import CaptureQueue, QueueFullError
from src.services.comfyui_service import APIConnectionError, APIError, TimeoutError
from src.services.comfyui_service_impl import ComfyUIService
from src.services.file_monitor_impl import FileMonitorServiceImpl
from src.services.file_monitor_service import FolderAccessError, FolderNotFoundError
from src.services.visual_feedback import IVisualFeedback


class ProcessingOrchestrator:
    """Orchestrator service for coordinating file monitoring, queue management, and ComfyUI processing.
    
    This service coordinates the end-to-end workflow:
    1. Monitors output folder for new JPEG files
    2. Enqueues captured images for processing
    3. Processes images through ComfyUI API
    4. Updates processing status and provides visual feedback
    """

    def __init__(
        self,
        settings: ApplicationSettings,
        visual_feedback: IVisualFeedback
    ):
        """Initialize the processing orchestrator.
        
        Args:
            settings: Application settings containing ComfyUI endpoint and workflow config
            visual_feedback: Service for visual feedback display
        """
        self._settings = settings
        self._visual_feedback = visual_feedback

        # Initialize services
        self._capture_queue = CaptureQueue(max_size=100)
        self._comfyui_service = ComfyUIService(
            endpoint=settings.comfyui_endpoint,
            timeout=settings.api_timeout
        )

        # File monitor callback
        self._file_monitor = FileMonitorServiceImpl(file_extensions=['.jpg', '.jpeg'])

        # State management
        self._running = False
        self._monitoring = False
        self._processing_thread: Optional[threading.Thread] = None
        self._status = ProcessingStatus(
            state='idle',
            current_image='',
            error_message='',
            queue_size=0
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
                on_file_created=self._on_file_created
            )
            self._monitoring = True
        except (FolderNotFoundError, FolderAccessError) as e:
            self._status = ProcessingStatus(
                state='error',
                current_image='',
                error_message=str(e),
                queue_size=0
            )
            self._visual_feedback.show_error_feedback(str(e))
            raise

        # Start processing worker thread
        self._processing_thread = threading.Thread(
            target=self._process_queue,
            daemon=True
        )
        self._processing_thread.start()

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
            return

        # Get file size
        try:
            filesize = Path(filepath).stat().st_size
        except OSError as e:
            self._visual_feedback.show_error_feedback(
                f"Could not read file size: {str(e)}"
            )
            return

        # Create ImageCapture object
        filename = Path(filepath).stem
        timestamp = filename.replace('capture_', '')

        image_capture = ImageCapture(
            timestamp=timestamp,
            filepath=filepath,
            filesize=filesize,
            output_folder=self._settings.output_folder,
            status='pending'
        )

        # Enqueue for processing
        try:
            self._capture_queue.enqueue(filepath)
            self._update_status()
            self._visual_feedback.show_processing_feedback()
        except QueueFullError:
            self._visual_feedback.show_error_feedback(
                "Processing queue is full. Image not added."
            )

    def _process_queue(self) -> None:
        """Worker thread that processes items from the queue."""
        while self._running:
            # Get next item from queue
            filepath = self._capture_queue.dequeue()

            if filepath is None:
                # Queue is empty, wait before checking again
                time.sleep(0.5)
                continue

            # Process the image
            self._process_image(filepath)

            # Update status
            self._update_status()

    def _process_image(self, filepath: str) -> None:
        """Process a single image through ComfyUI.
        
        Args:
            filepath: Path to the image to process.
        """
        # Update status to processing
        self._capture_queue.set_processing_state(ProcessingState.PROCESSING)
        self._capture_queue.set_current_image(filepath)
        self._update_status()

        try:
            # Load workflow JSON from file
            workflow_path = Path(self._settings.workflow_json_path)
            with open(workflow_path, 'r') as f:
                workflow_json = json.load(f)

            # Create ComfyUI workflow
            workflow = ComfyUIWorkflow(
                workflow_json=workflow_json,
                input_image_path=filepath,
                output_location=self._settings.output_folder
            )

            # Trigger workflow
            prompt_id = self._comfyui_service.trigger_workflow(
                workflow_json=workflow_json,
                input_image_path=filepath
            )

            # Wait for completion
            result = self._comfyui_service.wait_for_completion(prompt_id)

            # Update status to completed
            self._capture_queue.set_processing_state(ProcessingState.COMPLETED)
            self._capture_queue.set_current_image('')

            # Update image capture status
            image_capture = ImageCapture(
                timestamp=Path(filepath).stem.replace('capture_', ''),
                filepath=filepath,
                filesize=Path(filepath).stat().st_size,
                output_folder=self._settings.output_folder,
                status='completed'
            )

            if self._on_processing_complete:
                self._on_processing_complete(image_capture)

            self._visual_feedback.show_completion_feedback()

        except APIConnectionError as e:
            self._handle_processing_error(filepath, str(e))

        except APIError as e:
            self._handle_processing_error(filepath, str(e))

        except TimeoutError as e:
            self._handle_processing_error(filepath, str(e))

        except Exception as e:
            self._handle_processing_error(filepath, f"Unexpected error: {str(e)}")

    def _handle_processing_error(self, filepath: str, error_message: str) -> None:
        """Handle a processing error.
        
        Args:
            filepath: Path to the image that failed.
            error_message: Error message describing the failure.
        """
        # Update status to error
        self._capture_queue.set_processing_state(ProcessingState.ERROR, error_message)
        self._capture_queue.set_current_image('')

        # Update image capture status
        image_capture = ImageCapture(
            timestamp=Path(filepath).stem.replace('capture_', ''),
            filepath=filepath,
            filesize=Path(filepath).stat().st_size,
            output_folder=self._settings.output_folder,
            status='error'
        )

        if self._on_processing_error:
            self._on_processing_error(image_capture, error_message)

        self._visual_feedback.show_error_feedback(error_message)

    def _update_status(self) -> None:
        """Update the processing status."""
        state = self._capture_queue.get_processing_state().value
        current_image = self._capture_queue.get_current_image() or ''
        queue_size = self._capture_queue.get_queue_size()
        error_message = self._capture_queue.get_error_message() or ''

        self._status = ProcessingStatus(
            state=state,
            current_image=current_image,
            error_message=error_message,
            queue_size=queue_size
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

    def set_on_status_change(self, callback: Callable[[ProcessingStatus], None]) -> None:
        """Set callback for status changes.
        
        Args:
            callback: Function to call when status changes.
        """
        self._on_status_change = callback

    def set_on_processing_complete(self, callback: Callable[[ImageCapture], None]) -> None:
        """Set callback for processing completion.
        
        Args:
            callback: Function to call when processing completes.
        """
        self._on_processing_complete = callback

    def set_on_processing_error(self, callback: Callable[[ImageCapture, str], None]) -> None:
        """Set callback for processing errors.
        
        Args:
            callback: Function to call when processing fails.
        """
        self._on_processing_error = callback
