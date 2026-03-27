# API Documentation

**Feature**: Webcam-to-ComfyUI Desktop Application  
**Version**: 1.0.0  
**Date**: 2026-03-26

---

## Overview

This document provides detailed API documentation for the Webcam-to-ComfyUI Desktop Application. It covers all public interfaces, service contracts, and utility functions.

---

## Service Interfaces

### IWebcamService

Interface for webcam video capture operations.

```python
class IWebcamService:
    """Interface for webcam video capture operations."""
    
    def start(self) -> None:
        """Start the webcam video feed.
        
        Raises:
            WebcamNotFoundError: If no webcam is available.
            WebcamAccessError: If webcam access is denied.
        """
        pass
    
    def stop(self) -> None:
        """Stop the webcam video feed and release resources."""
        pass
    
    def capture_frame(self) -> bytes:
        """Capture the current video frame.
        
        Returns:
            bytes: JPEG-encoded image data.
            
        Raises:
            WebcamNotStartedError: If start() was not called.
            CaptureError: If frame capture fails.
        """
        pass
    
    def is_running(self) -> bool:
        """Check if the webcam is currently running.
        
        Returns:
            bool: True if running, False otherwise.
        """
        pass
```

---

### IFileMonitorService

Interface for monitoring a folder for new files.

```python
from typing import Callable, Optional

class IFileMonitorService:
    """Interface for monitoring a folder for new files."""
    
    def start_monitoring(self, folder_path: str, on_file_created: Callable[[str], None]) -> None:
        """Start monitoring a folder for new files.
        
        Args:
            folder_path: Path to the folder to monitor.
            on_file_created: Callback function called when a new file is created.
                            Receives the full file path as argument.
        
        Raises:
            FolderNotFoundError: If the folder does not exist.
            FolderAccessError: If folder access is denied.
        """
        pass
    
    def stop_monitoring(self) -> None:
        """Stop monitoring the folder."""
        pass
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is currently active.
        
        Returns:
            bool: True if monitoring, False otherwise.
        """
        pass
```

---

### IComfyUIService

Interface for ComfyUI API communication.

```python
from typing import Dict, Any, Optional

class IComfyUIService:
    """Interface for ComfyUI API communication."""
    
    def __init__(self, endpoint: str, timeout: int = 30):
        """Initialize the ComfyUI service.
        
        Args:
            endpoint: ComfyUI API endpoint URL.
            timeout: Request timeout in seconds.
        """
        pass
    
    def trigger_workflow(self, workflow_json: Dict[str, Any], input_image_path: str) -> str:
        """Trigger a ComfyUI workflow.
        
        Args:
            workflow_json: The ComfyUI workflow configuration.
            input_image_path: Path to the input image.
        
        Returns:
            str: The prompt ID for tracking the workflow.
        
        Raises:
            APIConnectionError: If connection to ComfyUI fails.
            APIError: If ComfyUI returns an error response.
            TimeoutError: If request times out.
        """
        pass
    
    def check_status(self, prompt_id: str) -> Dict[str, Any]:
        """Check the status of a workflow.
        
        Args:
            prompt_id: The prompt ID returned from trigger_workflow().
        
        Returns:
            Dict[str, Any]: Workflow status information.
        
        Raises:
            APIConnectionError: If connection to ComfyUI fails.
            APIError: If ComfyUI returns an error response.
            TimeoutError: If request times out.
        """
        pass
    
    def is_available(self) -> bool:
        """Check if ComfyUI API is accessible.
        
        Returns:
            bool: True if API is available, False otherwise.
        """
        pass
```

---

### ICaptureQueue

Interface for managing the capture queue.

```python
from typing import Optional
from enum import Enum

class ProcessingState(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class ICaptureQueue:
    """Interface for managing the capture queue."""
    
    def enqueue(self, image_path: str) -> None:
        """Add an image to the processing queue.
        
        Args:
            image_path: Path to the image to process.
        """
        pass
    
    def dequeue(self) -> Optional[str]:
        """Remove and return the next image from the queue.
        
        Returns:
            Optional[str]: Path to the next image, or None if queue is empty.
        """
        pass
    
    def get_queue_size(self) -> int:
        """Get the current queue size.
        
        Returns:
            int: Number of images waiting in queue.
        """
        pass
    
    def get_processing_state(self) -> ProcessingState:
        """Get the current processing state.
        
        Returns:
            ProcessingState: Current state of processing.
        """
        pass
    
    def set_processing_state(self, state: ProcessingState, error_message: Optional[str] = None) -> None:
        """Set the current processing state.
        
        Args:
            state: New processing state.
            error_message: Error message if state is ERROR.
        """
        pass
    
    def is_processing(self) -> bool:
        """Check if processing is currently active.
        
        Returns:
            bool: True if processing, False otherwise.
        """
        pass
```

---

## UI Contracts

### IVisualFeedback

Interface for visual feedback display.

```python
from typing import Literal

class IVisualFeedback:
    """Interface for visual feedback display."""
    
    def show_capture_feedback(self) -> None:
        """Show visual feedback for image capture."""
        pass
    
    def show_processing_feedback(self) -> None:
        """Show visual feedback for processing start."""
        pass
    
    def show_completion_feedback(self) -> None:
        """Show visual feedback for processing completion."""
        pass
    
    def show_error_feedback(self, message: str) -> None:
        """Show visual feedback for errors.
        
        Args:
            message: Error message to display.
        """
        pass
    
    def hide_feedback(self) -> None:
        """Hide all visual feedback."""
        pass
```

---

## Data Models

### ImageCapture

Represents a single frame captured from the webcam.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `timestamp` | `str` | Yes | Format: `YYYYMMDD_HHmmss` | Timestamp of capture |
| `filepath` | `str` | Yes | Valid file path | Full path to saved JPEG |
| `filesize` | `int` | Yes | >= 0 | Size of file in bytes |
| `output_folder` | `str` | Yes | Valid directory path | Directory where saved |
| `status` | `str` | Yes | `pending`, `processing`, `completed`, `error` | Current processing status |

---

### ApplicationSettings

Represents user-configurable application preferences.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `output_folder` | `str` | Yes | Valid directory path | Directory for captured images |
| `comfyui_endpoint` | `str` | Yes | Valid URL format | ComfyUI API endpoint |
| `workflow_json_path` | `str` | Yes | Valid file path | Path to workflow JSON |
| `api_timeout` | `int` | No | >= 1, default: 30 | Request timeout in seconds |

---

### ComfyUIWorkflow

Represents the art style processing configuration.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `workflow_json` | `dict` | Yes | Valid JSON structure | ComfyUI workflow config |
| `input_image_path` | `str` | Yes | Valid file path | Path to input image |
| `output_location` | `str` | Yes | Valid directory path | Directory for processed images |
| `prompt_id` | `str` | No | UUID format | ComfyUI prompt ID |

---

### ProcessingStatus

Represents the current state of image processing.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `state` | `str` | Yes | `idle`, `processing`, `completed`, `error` | Current processing state |
| `current_image` | `str` | No | Valid file path | Image currently being processed |
| `error_message` | `str` | No | Max 1000 chars | Error message if state is `error` |
| `queue_size` | `int` | Yes | >= 0 | Number of images in queue |

---

## Error Types

| Error Type | User Message | Recovery Action |
|------------|--------------|-----------------|
| `WebcamNotFoundError` | "No webcam detected. Please connect a webcam and try again." | Connect webcam |
| `WebcamAccessError` | "Cannot access webcam. Close other applications using the webcam and try again." | Close other apps |
| `FolderNotFoundError` | "Output folder not found. Please select a valid folder in settings." | Select valid folder |
| `FolderAccessError` | "Cannot access output folder. Check permissions and try again." | Check permissions |
| `APIConnectionError` | "Cannot connect to ComfyUI. Make sure ComfyUI is running and try again." | Start ComfyUI |
| `APIError` | "ComfyUI returned an error. Check the workflow configuration and try again." | Check workflow |
| `TimeoutError` | "Request to ComfyUI timed out. Check your network connection and try again." | Retry request |

---

## Utility Functions

### FileUtils

```python
class FileUtils:
    """Utility class for file operations."""
    
    @staticmethod
    def generate_unique_filename(prefix: str = 'capture', suffix: str = '.jpg') -> str:
        """Generate a unique filename with timestamp.
        
        Args:
            prefix: Filename prefix (default: 'capture')
            suffix: Filename suffix (default: '.jpg')
        
        Returns:
            str: Unique filename in format '{prefix}_YYYYMMDD_HHmmss{suffix}'
        """
        pass
    
    @staticmethod
    def wait_for_file_ready(filepath: str, timeout: int = 5) -> bool:
        """Wait for a file to be fully written.
        
        Args:
            filepath: Path to the file to check.
            timeout: Maximum time to wait in seconds (default: 5).
        
        Returns:
            bool: True if file is ready, False if timeout reached.
        """
        pass
```

---

### ErrorManager

```python
class ErrorManager:
    """Utility class for error handling."""
    
    def handle_error(self, error: Exception, user_message: str) -> None:
        """Handle an error and display user-friendly message.
        
        Args:
            error: The exception that occurred.
            user_message: User-friendly message to display.
        """
        pass
    
    def get_recovery_action(self, error_type: str) -> str:
        """Get recovery action for an error type.
        
        Args:
            error_type: Type of error (e.g., 'WebcamNotFoundError').
        
        Returns:
            str: Recovery action description.
        """
        pass
```

---

## Service Implementations

### CaptureService

Main service for image capture operations.

```python
class CaptureService:
    """Service for image capture operations."""
    
    def __init__(self, webcam_service: IWebcamService, 
                 settings: ApplicationSettings,
                 visual_feedback: IVisualFeedback):
        """Initialize the capture service.
        
        Args:
            webcam_service: Webcam service instance.
            settings: Application settings.
            visual_feedback: Visual feedback service.
        """
        pass
    
    def capture_and_save(self) -> Optional[ImageCapture]:
        """Capture a frame and save to output folder.
        
        Returns:
            Optional[ImageCapture]: ImageCapture object if successful, None otherwise.
        """
        pass
    
    def get_current_frame(self) -> Optional[bytes]:
        """Get current frame without saving.
        
        Returns:
            Optional[bytes]: JPEG-encoded frame data, or None if capture fails.
        """
        pass
```

---

### ProcessingOrchestrator

Coordinates file monitoring, queue management, and ComfyUI processing.

```python
class ProcessingOrchestrator:
    """Orchestrates the complete capture-to-processing workflow."""
    
    def __init__(self, file_monitor: IFileMonitorService,
                 capture_queue: ICaptureQueue,
                 comfyui_service: IComfyUIService):
        """Initialize the orchestrator.
        
        Args:
            file_monitor: File monitor service instance.
            capture_queue: Capture queue instance.
            comfyui_service: ComfyUI service instance.
        """
        pass
    
    def start(self) -> None:
        """Start the orchestrator."""
        pass
    
    def stop(self) -> None:
        """Stop the orchestrator."""
        pass
    
    def on_file_created(self, filepath: str) -> None:
        """Handle new file creation event.
        
        Args:
            filepath: Path to the newly created file.
        """
        pass
```

---

## ComfyUI API Endpoints

The application uses the following ComfyUI API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/prompt` | POST | Submit workflow with inputs |
| `/history/{prompt_id}` | GET | Check workflow status |
| `/view/{filename}` | GET | Retrieve output images |

---

## Configuration

### ComfyUI Endpoint

Default: `http://127.0.0.1:8188`

The endpoint can be configured in the application settings dialog.

### API Timeout

Default: 30 seconds

Configurable in the application settings dialog.

---

## Logging

All services use structured logging with the following format:

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [Component] Message
```

Log levels:
- `DEBUG`: Detailed debugging information
- `INFO`: General information about operations
- `WARNING`: Non-critical issues
- `ERROR`: Error conditions
- `CRITICAL`: Critical errors

---

## Testing

### Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Contract tests
pytest tests/contract/ -v

# All tests
pytest -v
```

### Test Coverage

Target: 80%+ code coverage

---

## Support

For issues or questions:
1. Check the troubleshooting section in quickstart.md
2. Review the full specification at `specs/003-webcam-comfyui-integration/spec.md`
3. Check the implementation plan at `specs/003-webcam-comfyui-integration/plan.md`
