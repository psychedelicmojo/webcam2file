import sys

from src.models.application_settings import ApplicationSettings
from src.services.capture_service import CaptureService
from src.services.comfyui_service_impl import ComfyUIService
from src.services.email_service_impl import GoogleAppsScriptEmailService
from src.services.file_monitor_impl import FileMonitorServiceImpl
from src.services.processing_orchestrator import ProcessingOrchestrator
from src.services.settings_service import SettingsService
from src.services.visual_feedback import VisualFeedback
from src.services.webcam_impl import WebcamServiceImpl
from src.ui.main_window import MainWindow


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


def load_and_validate_settings():
    """Load and validate settings from settings.json.

    Returns:
        ApplicationSettings if valid, None if settings are invalid or missing
    """
    settings_service = SettingsService()

    try:
        # Load settings from file
        settings = settings_service.load_settings()
        print("Loaded settings from settings.json")

        # Validate output folder exists and is writable
        if not settings_service.ensure_output_folder_exists(settings):
            print(f"Warning: Output folder is not accessible: {settings.output_folder}")
            return None

        # Test ComfyUI connection if enabled
        if settings.is_comfyui_enabled():
            result = settings_service.test_connection(settings)
            if result.get("success") != "true":
                print(
                    f"Warning: ComfyUI connection test failed: {result.get('message')}"
                )
                print(
                    "ComfyUI will be disabled. Images will be captured but not processed."
                )
                # Return settings but with ComfyUI disabled
                settings.enable_comfyui = False
                return settings
            print(f"ComfyUI connection test passed: {result.get('message')}")

        return settings

    except FileNotFoundError as e:
        print(f"Warning: Settings file not found: {e}")
        return None
    except ValueError as e:
        print(f"Warning: Invalid settings: {e}")
        return None
    except Exception as e:
        print(f"Warning: Error loading settings: {e}")
        return None


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

    # Load and validate settings from settings.json
    settings = load_and_validate_settings()

    # Fallback to defaults if settings are invalid or missing
    if settings is None:
        print("Using default settings (ComfyUI disabled)...")
        from src.models.application_settings import WorkflowConfig

        settings = ApplicationSettings(
            output_folder="captures",
            comfyui_endpoint="http://127.0.0.1:8188",
            workflow_configs=[WorkflowConfig(name="", path="") for _ in range(4)],
            api_timeout=30,
            enable_comfyui=False,  # Disable ComfyUI if settings are invalid
        )

    # Initialize services
    webcam_service = WebcamServiceImpl(
        webcam_index=0
    )  # Change index to select different webcam
    visual_feedback = VisualFeedback()
    file_monitor_service = FileMonitorServiceImpl()

    # Create capture service (requires output folder)
    capture_service = CaptureService(
        webcam_service=webcam_service,
        visual_feedback=visual_feedback,
        output_folder=settings.output_folder,
    )

    # Initialize ComfyUI service only if enabled
    comfyui_service = None
    orchestrator = None
    if settings.is_comfyui_enabled():
        try:
            comfyui_service = ComfyUIService(endpoint=settings.comfyui_endpoint)
            orchestrator = ProcessingOrchestrator(settings, visual_feedback)
            print("ComfyUI integration enabled")
        except Exception as e:
            print(f"Warning: Could not initialize ComfyUI: {e}")
            print("Running in webcam capture mode only.")

    # Initialize email service (works even without an Apps Script URL configured)
    email_service = GoogleAppsScriptEmailService(
        apps_script_url=settings.apps_script_url,
        timeout=settings.api_timeout,
    )

    # Create and run main window
    app = MainWindow(
        webcam_service=webcam_service,
        capture_service=capture_service,
        visual_feedback=visual_feedback,
        file_monitor_service=file_monitor_service,
        comfyui_service=comfyui_service,
        orchestrator=orchestrator,
        email_service=email_service,
        initial_email=settings.email_address,
        initial_countdown=settings.countdown_seconds,
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
