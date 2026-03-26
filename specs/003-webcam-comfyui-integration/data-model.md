# Data Model: Webcam-to-ComfyUI Desktop Application

**Feature Branch**: `003-webcam-comfyui-integration`  
**Date**: 2026-03-25

---

## Entity Overview

| Entity | Description | Key Attributes | Relationships |
|--------|-------------|----------------|---------------|
| [`ImageCapture`](#imagecapture) | A single frame captured from the webcam | timestamp, filepath, filesize, output_folder | Created by [`CaptureService`](src/services/capture_service.py) |
| [`ApplicationSettings`](#applicationsettings) | User-configurable application preferences | output_folder, comfyui_endpoint, workflow_json_path | Loaded by [`SettingsManager`](src/services/settings_service.py) |
| [`ComfyUIWorkflow`](#comfyuiworkflow) | Art style processing configuration | workflow_json, input_image_path, output_location | Executed by [`ComfyUIService`](src/services/comfyui_service.py) |
| [`ProcessingStatus`](#processingstatus) | Current state of image processing | state, current_image, error_message | Updated by [`CaptureQueue`](src/services/capture_queue.py) |

---

## Entity Details

### ImageCapture

Represents a single frame captured from the webcam.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `timestamp` | `str` | Yes | Format: `YYYYMMDD_HHmmss` | Timestamp of capture in `capture_YYYYMMDD_HHmmss.jpg` format |
| `filepath` | `str` | Yes | Valid file path | Full path to the saved JPEG file |
| `filesize` | `int` | Yes | >= 0 | Size of the file in bytes |
| `output_folder` | `str` | Yes | Valid directory path | Directory where the image was saved |
| `status` | `str` | Yes | One of: `pending`, `processing`, `completed`, `error` | Current processing status |

**State Transitions**:
```
pending → processing → completed
pending → processing → error
```

**Validation Rules**:
- `timestamp` must match pattern `YYYYMMDD_HHmmss`
- `filepath` must end with `.jpg` extension
- `filesize` must be greater than 0
- `output_folder` must be a valid directory path

---

### ApplicationSettings

Represents user-configurable application preferences.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `output_folder` | `str` | Yes | Valid directory path | Directory where captured images are saved |
| `comfyui_endpoint` | `str` | Yes | Valid URL format | ComfyUI API endpoint (e.g., `http://127.0.0.1:8188`) |
| `workflow_json_path` | `str` | Yes | Valid file path | Path to the ComfyUI workflow JSON file |
| `api_timeout` | `int` | No | >= 1, default: 30 | Timeout in seconds for API requests |

**Validation Rules**:
- `output_folder` must exist and be writable
- `comfyui_endpoint` must be a valid HTTP/HTTPS URL
- `workflow_json_path` must point to an existing JSON file
- `api_timeout` must be at least 1 second

---

### ComfyUIWorkflow

Represents the art style processing configuration.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `workflow_json` | `dict` | Yes | Valid JSON structure | The ComfyUI workflow configuration |
| `input_image_path` | `str` | Yes | Valid file path | Path to the input image for processing |
| `output_location` | `str` | Yes | Valid directory path | Directory where processed images are saved |
| `prompt_id` | `str` | No | UUID format | ComfyUI prompt ID returned from API |

**Validation Rules**:
- `workflow_json` must contain valid ComfyUI workflow structure
- `input_image_path` must point to an existing file
- `output_location` must be a valid directory path

---

### ProcessingStatus

Represents the current state of image processing.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `state` | `str` | Yes | One of: `idle`, `processing`, `completed`, `error` | Current processing state |
| `current_image` | `str` | No | Valid file path | Path to the image currently being processed |
| `error_message` | `str` | No | Max 1000 chars | Error message if state is `error` |
| `queue_size` | `int` | Yes | >= 0 | Number of images waiting in queue |

**State Transitions**:
```
idle → processing → completed → idle
idle → processing → error → idle
```

**Validation Rules**:
- `state` must be one of the allowed values
- `current_image` must be set when state is `processing`
- `error_message` must be set when state is `error`
- `queue_size` must be non-negative

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                            User Action                              │
│                         (Space Bar Press)                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        CaptureService                               │
│  - Captures frame from webcam                                       │
│  - Creates ImageCapture entity                                      │
│  - Saves JPEG to output folder                                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FileMonitorService                             │
│  - Monitors output folder for new files                            │
│  - Detects new JPEG files                                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         CaptureQueue                                │
│  - Queues captures for processing                                   │
│  - Manages processing order                                         │
│  - Updates ProcessingStatus                                         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        ComfyUIService                               │
│  - Loads ApplicationSettings                                        │
│  - Creates ComfyUIWorkflow                                          │
│  - Sends request to ComfyUI API                                     │
│  - Updates ProcessingStatus                                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Persistence Strategy

| Entity | Storage | Format | Access Pattern |
|--------|---------|--------|----------------|
| `ImageCapture` | In-memory | Python object | Read during processing, discarded after completion |
| `ApplicationSettings` | File system | JSON file | Read on startup, written on settings change |
| `ComfyUIWorkflow` | In-memory | Python object | Created per capture, discarded after processing |
| `ProcessingStatus` | In-memory | Python object | Updated during processing lifecycle |

**Notes**:
- `ImageCapture` and `ComfyUIWorkflow` are transient entities created during processing
- `ApplicationSettings` persists user preferences across application sessions
- `ProcessingStatus` tracks current processing state in memory

---

## Testing Strategy

### Unit Tests
- [`ImageCapture`](src/models/image_capture.py): Validate timestamp format, filepath validation
- [`ApplicationSettings`](src/models/application_settings.py): Validate URL format, file existence checks
- [`ComfyUIWorkflow`](src/models/comfyui_workflow.py): Validate workflow JSON structure
- [`ProcessingStatus`](src/models/processing_status.py): Validate state transitions

### Integration Tests
- Full capture → save → monitor → process workflow
- Error handling: no webcam, API unavailable, folder inaccessible
- Queue behavior: multiple captures in quick succession
