import sys

from src.ui.main_window import MainWindow
from src.services.webcam_impl import WebcamServiceImpl
from src.services.capture_service import CaptureService
from src.services.visual_feedback import VisualFeedback
from src.services.file_monitor_impl import FileMonitorServiceImpl
from src.services.comfyui_service_impl import ComfyUIService
from src.services.processing_orchestrator import ProcessingOrchestrator
from src.models.application_settings import ApplicationSettings


def list_webcams():
    """List all available webcams."""
    print("Available webcams:")
    webcams = WebcamServiceImpl.list_available_webcams()
    if not webcams:
        print("  No webcams found.")
        return
    for index, name in webcams:
        print(f"  [{index}] {name}")
    return webcams


def main():
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--list", "-l"]:
            list_webcams()
            return
        elif sys.argv[1] in ["--help", "-h"]:
            print("Usage: python main.py [OPTIONS]")
            print()
            print("Options:")
            print("  --list, -l    List available webcams")
            print("  --help, -h    Show this help message")
            print()
            print("Examples:")
            print("  python main.py              # Run with default webcam (index 0)")
            print("  python main.py --list       # List available webcams")
            return

    # Initialize settings - ComfyUI is optional
    # Set enable_comfyui=False to use webcam capture without ComfyUI
    settings = ApplicationSettings(
        output_folder="captures",
        comfyui_endpoint="http://127.0.0.1:8000",
        workflow_json_path="workflows/flux_kontext_dev_basic_api.json",
        api_timeout=90,
        enable_comfyui=True  # Set to True to enable ComfyUI processing
    )
    
    # Initialize services
    webcam_service = WebcamServiceImpl(webcam_index=0)  # Change index to select different webcam
    visual_feedback = VisualFeedback()
    file_monitor_service = FileMonitorServiceImpl()
    
    # Create capture service (requires output folder)
    capture_service = CaptureService(
        webcam_service=webcam_service,
        visual_feedback=visual_feedback,
        output_folder=settings.output_folder
    )
    
    # Initialize ComfyUI service only if enabled
    comfyui_service = None
    orchestrator = None
    if settings.is_comfyui_enabled():
        try:
            comfyui_service = ComfyUIService(endpoint=settings.comfyui_endpoint)
            orchestrator = ProcessingOrchestrator(settings, visual_feedback)
        except Exception as e:
            print(f"Warning: Could not initialize ComfyUI: {e}")
            print("Running in webcam capture mode only.")
    
    # Create and run main window
    # Use the existing root window (MainWindow creates its own, so we don't need this)
    app = MainWindow(
        webcam_service=webcam_service,
        capture_service=capture_service,
        visual_feedback=visual_feedback,
        file_monitor_service=file_monitor_service,
        comfyui_service=comfyui_service,
        orchestrator=orchestrator
    )
    
    # Start the application (video feed and event loop)
    try:
        app.start()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
