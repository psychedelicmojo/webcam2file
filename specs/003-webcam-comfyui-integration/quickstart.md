# Quick Start Guide: Webcam-to-ComfyUI Desktop Application

**Feature Branch**: `003-webcam-comfyui-integration`  
**Date**: 2026-03-25

---

## Prerequisites

Before running the application, ensure the following are installed:

### System Requirements
- **Operating System**: Windows 11 (64-bit)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space
- **Webcam**: High-definition webcam (1080p or better)

### Software Dependencies
- **Python**: 3.11 or later
- **ComfyUI**: Running locally on `http://127.0.0.1:8188`

### Python Packages
```bash
pip install opencv-python pillow requests watchdog pytest
```

---

## Installation

1. **Clone the repository** (if applicable):
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

---

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

---

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
|-- ---|------- |
| Space Bar | Capture current frame |
| Escape | Close application |
| Ctrl+, | Open Settings dialog |

---

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

---

## Testing

### Run Unit Tests
```bash
pytest tests/unit/ -v
```

### Run Integration Tests
```bash
pytest tests/integration/ -v
```

### Run Contract Tests
```bash
pytest tests/contract/ -v
```

---

## Development

### Project Structure
```
src/
├── models/              # Data models
├── services/            # Business logic services
├── ui/                  # UI presentation layer
└── lib/                 # Shared utilities

tests/
├── contract/            # Contract tests
├── integration/         # Integration tests
└── unit/                # Unit tests
```

### Adding New Features
1. Update the feature specification
2. Run `/speckit.plan` to generate implementation plan
3. Write tests first (TDD)
4. Implement code to make tests pass
5. Update documentation

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the full specification at `specs/003-webcam-comfyui-integration/spec.md`
3. Check the implementation plan at `specs/003-webcam-comfyui-integration/plan.md`
