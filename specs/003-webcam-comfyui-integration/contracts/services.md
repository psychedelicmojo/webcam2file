# Contracts: Webcam-to-ComfyUI Desktop Application

**Feature Branch**: `003-webcam-comfyui-integration`  
**Date**: 2026-03-25

---

## Overview

This document defines the interface contracts for the Webcam-to-ComfyUI Desktop Application. Contracts specify the expected behavior of services and components, enabling test-driven development and ensuring proper decoupling.

---

## Service Contracts

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

**Test Cases**:
1. `test_start_success`: Verify start() initializes webcam without errors
2. `test_start_no_webcam`: Verify WebcamNotFoundError when no webcam available
3. `test_capture_frame`: Verify capture_frame() returns valid JPEG data
4. `test_stop`: Verify stop() releases webcam resources

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

**Test Cases**:
1. `test_start_monitoring_success`: Verify monitoring starts without errors
2. `test_file_detected`: Verify callback is called when new file is created
3. `test_stop_monitoring`: Verify monitoring stops cleanly
4. `test_multiple_files`: Verify all files are detected in sequence

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

**Test Cases**:
1. `test_trigger_workflow_success`: Verify workflow is triggered successfully
2. `test_check_status`: Verify status check returns correct information
3. `test_api_unavailable`: Verify APIConnectionError when ComfyUI is down
4. `test_timeout`: Verify TimeoutError when request exceeds timeout

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

**Test Cases**:
1. `test_enqueue_dequeue`: Verify items are processed in FIFO order
2. `test_queue_size`: Verify queue size updates correctly
3. `test_state_transitions`: Verify state transitions are correct
4. `test_empty_queue`: Verify dequeue returns None when queue is empty

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

**Test Cases**:
1. `test_capture_feedback`: Verify feedback appears on capture
2. `test_processing_feedback`: Verify feedback appears on processing start
3. `test_completion_feedback`: Verify feedback appears on completion
4. `test_error_feedback`: Verify error message is displayed

---

## Error Contracts

### Error Types

| Error Type | HTTP Code | User Message | Recovery Action |
|------------|-----------|--------------|-----------------|
| `WebcamNotFoundError` | N/A | "No webcam detected. Please connect a webcam and try again." | Connect webcam |
| `WebcamAccessError` | N/A | "Cannot access webcam. Close other applications using the webcam and try again." | Close other apps |
| `FolderNotFoundError` | N/A | "Output folder not found. Please select a valid folder in settings." | Select valid folder |
| `FolderAccessError` | N/A | "Cannot access output folder. Check permissions and try again." | Check permissions |
| `APIConnectionError` | N/A | "Cannot connect to ComfyUI. Make sure ComfyUI is running and try again." | Start ComfyUI |
| `APIError` | Varies | "ComfyUI returned an error. Check the workflow configuration and try again." | Check workflow |
| `TimeoutError` | N/A | "Request to ComfyUI timed out. Check your network connection and try again." | Retry request |

---

## Testing Strategy

### Contract Test Scenarios

1. **Full Workflow Test**:
   - Start webcam service
   - Monitor folder for new files
   - Capture image via space bar
   - Verify file is detected
   - Trigger ComfyUI workflow
   - Verify processing completes

2. **Error Handling Tests**:
   - No webcam available
   - ComfyUI API unavailable
   - Output folder inaccessible
   - API timeout

3. **Queue Tests**:
   - Multiple captures in quick succession
   - Queue processes items in order
   - Queue handles errors gracefully
