# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the application
python main.py

# List available webcams
python main.py --list

# Run all tests
pytest -v

# Run a single test file
pytest tests/unit/test_application_settings.py -v

# Run a specific test
pytest tests/contract/test_webcam_service.py::TestWebcamServiceContract::test_start_success -v

# Run with coverage
pytest --cov=src --cov-report=html

# Lint
ruff check .

# Format
ruff format .
```

## Architecture

The app is a Windows desktop application (tkinter + OpenCV) that:
1. Shows a live webcam feed
2. Captures frames on Space Bar press, saving JPEGs to `captures/`
3. Optionally sends captured images through a local ComfyUI workflow (image-to-image AI processing)

### Dependency injection pattern

`main.py` wires all services together and passes them into `MainWindow`. Every service is backed by an abstract interface (`IWebcamService`, `IComfyUIService`, `IFileMonitorService`) with a concrete `*Impl` class. Tests use mock implementations against the interface contracts.

### Processing pipeline (full ComfyUI mode)

`ProcessingOrchestrator` coordinates the end-to-end flow after capture:
- `FileMonitorServiceImpl` (watchdog) detects new JPEGs in the output folder
- `CaptureQueue` holds filepaths awaiting processing
- A worker thread dequeues items and calls `ComfyUIService` with retry logic (3 attempts, 2s delay for transient errors)
- `ComfyUIService` uploads the image, patches the workflow JSON (updates `LoadImage` node, randomizes `KSampler` seed), triggers the prompt, polls for completion, then downloads outputs

### Settings

Settings are persisted to `settings.json` at the repo root via `SettingsService`. `ApplicationSettings` holds:
- `output_folder` — where captures and processed outputs land
- `comfyui_endpoint` — default `http://127.0.0.1:8188`
- `workflow_configs` — exactly 4 slots, each with a `name` and `path` to a ComfyUI workflow JSON
- `art_styles` — exactly 5 slots (currently unused in processing logic)

ComfyUI is disabled automatically on startup if the connection test fails; the app falls back to capture-only mode.

### Test structure

- `tests/contract/` — interface compliance tests using mock implementations
- `tests/integration/` — user story end-to-end tests (4 user stories)
- `tests/unit/` — pure unit tests for models and utilities
