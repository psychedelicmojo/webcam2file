"""Debug video feed in the actual application."""

import logging
import tkinter as tk

from src.models.application_settings import ApplicationSettings
from src.services.capture_service import CaptureService
from src.services.file_monitor_impl import FileMonitorServiceImpl
from src.services.visual_feedback import VisualFeedback
from src.services.webcam_impl import WebcamServiceImpl
from src.ui.main_window import MainWindow

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)


def main():
    # Initialize settings
    settings = ApplicationSettings(
        output_folder="captures",
        comfyui_endpoint="http://127.0.0.1:8188",
        workflow_json_path="workflow.json",
        api_timeout=30,
        enable_comfyui=False,
    )

    # Initialize services
    webcam_service = WebcamServiceImpl(webcam_index=0)
    visual_feedback = VisualFeedback()
    file_monitor_service = FileMonitorServiceImpl()

    # Create capture service
    capture_service = CaptureService(
        webcam_service=webcam_service,
        visual_feedback=visual_feedback,
        output_folder=settings.output_folder,
    )

    # Create and run main window
    tk.Tk()
    app = MainWindow(
        webcam_service=webcam_service,
        capture_service=capture_service,
        visual_feedback=visual_feedback,
        file_monitor_service=file_monitor_service,
        comfyui_service=None,
        orchestrator=None,
    )

    # Start the application
    try:
        app.start()
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
