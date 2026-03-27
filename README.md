# Webcam-to-ComfyUI Desktop Application

A desktop application that displays a live video feed from a connected high-definition webcam. When the user presses the space bar, the current frame is captured and saved as a JPEG image to a monitored local folder. The application continuously monitors this folder and, upon detecting a new image file, automatically triggers a local ComfyUI workflow via its API to apply an art style.

## Features

- **Live Video Feed**: Displays real-time video from HD webcam (1920x1080)
- **Image Capture**: Press space bar to capture current frame as JPEG
- **Folder Monitoring**: Automatically detects new images in output folder
- **ComfyUI Integration**: Triggers art style processing via local ComfyUI API
- **Visual Feedback**: Shows capture events and processing status
- **Queue Management**: Handles multiple captures in sequence
- **Error Handling**: Graceful error recovery with user-friendly messages
- **Configurable Settings**: Customize output folder, ComfyUI endpoint, and workflow

## Prerequisites

### System Requirements
- **Operating System**: Windows 11 (64-bit)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space
- **Webcam**: High-definition webcam (1080p or better)

### Software Dependencies
- **Python**: 3.11 or later
- **ComfyUI**: Running locally on `http://127.0.0.1:8188`

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd webcam2file
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```bash
   python -c "import cv2; print('OpenCV version:', cv2.__version__)"
   python -c "from PIL import Image; print('Pillow installed')"
   python -c "import requests; print('Requests installed')"
   python -c "from watchdog.observers import Observer; print('Watchdog installed')"
   ```

## Configuration

### First-Time Setup

1. **Launch the application**:
   ```bash
   python -m src.main
   ```

2. **Configure output folder**:
   - Open Settings from the application menu
   - Click "Select Output Folder"
   - Choose a directory where captured images will be saved

3. **Configure ComfyUI workflow**:
   - In Settings, click "Select Workflow JSON"
   - Choose your pre-saved ComfyUI workflow JSON file
   - Verify ComfyUI endpoint is `http://127.0.0.1:8188`

4. **Test configuration**:
   - Click "Test Connection" to verify ComfyUI is accessible
   - Click "Test Capture" to verify webcam is working

## Usage

### Basic Workflow

1. **Start the application**:
   ```bash
   python -m src.main
   ```

2. **Capture an image**:
   - Ensure the webcam feed is visible
   - Press the **Space Bar** to capture the current frame
   - Wait for visual feedback (subtle flash/border highlight)

3. **Monitor processing**:
   - The application automatically detects the new image
   - Visual feedback indicates processing has started
   - Processing completion is indicated by another visual feedback

4. **View results**:
   - Processed images are saved to the configured output folder
   - Open the folder to view your art-styled images

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space Bar | Capture current frame |
| Escape | Close application |
| Ctrl+, | Open Settings dialog |

## Troubleshooting

### No Webcam Detected

**Error**: "No webcam available"

**Solutions**:
1. Check that the webcam is connected
2. Close other applications using the webcam
3. Restart the application

### ComfyUI Connection Failed

**Error**: "Cannot connect to ComfyUI"

**Solutions**:
1. Ensure ComfyUI is running locally
2. Verify ComfyUI is accessible at `http://127.0.0.1:8188`
3. Check ComfyUI logs for errors

### Output Folder Inaccessible

**Error**: "Cannot access output folder"

**Solutions**:
1. Verify the folder path is correct
2. Check folder permissions
3. Select a different folder in Settings

### Queue Full

**Error**: "Processing queue is full"

**Solutions**:
1. Wait for current processing to complete
2. Reduce the number of rapid captures
3. Check ComfyUI is processing workflows

## Development

### Project Structure

```
src/
├── models/              # Data models
│   ├── image_capture.py
│   ├── application_settings.py
│   ├── comfyui_workflow.py
│   └── processing_status.py
├── services/            # Business logic services
│   ├── webcam_service.py
│   ├── file_monitor_service.py
│   ├── comfyui_service.py
│   ├── capture_queue.py
│   ├── capture_service.py
│   ├── file_monitor_impl.py
│   ├── comfyui_service_impl.py
│   ├── capture_queue_impl.py
│   ├── processing_orchestrator.py
│   └── settings_service.py
├── ui/                  # UI presentation layer
│   ├── main_window.py
│   └── settings_dialog.py
└── lib/                 # Shared utilities
    ├── error_manager.py
    └── file_utils.py

tests/
├── contract/            # Contract tests
│   ├── test_webcam_service.py
│   ├── test_capture_service.py
│   ├── test_file_monitor_service.py
│   ├── test_comfyui_service.py
│   └── test_capture_queue.py
├── integration/         # Integration tests
│   ├── test_user_story_1.py
│   ├── test_user_story_2.py
│   ├── test_user_story_3.py
│   └── test_user_story_4.py
└── unit/                # Unit tests
    ├── test_application_settings.py
    └── test_error_manager.py
```

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

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Run linter
ruff check .

# Format code
ruff format .
```

## API Documentation

See [`docs/API.md`](docs/API.md) for detailed API documentation.

## License

MIT License - See LICENSE file for details.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the full specification at `specs/003-webcam-comfyui-integration/spec.md`
3. Check the implementation plan at `specs/003-webcam-comfyui-integration/plan.md`
