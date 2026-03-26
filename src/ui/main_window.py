"""Main window UI for the Webcam-to-ComfyUI Desktop Application."""

import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

import cv2
from PIL import Image, ImageTk

from src.services.capture_service import CaptureService
from src.services.comfyui_service import IComfyUIService
from src.services.file_monitor_service import IFileMonitorService
from src.services.processing_orchestrator import ProcessingOrchestrator
from src.services.settings_service import SettingsService
from src.services.visual_feedback import IVisualFeedback
from src.services.webcam_service import IWebcamService
from src.ui.settings_dialog import SettingsDialog


class MainWindow:
    """Main application window for webcam capture and processing.

    This window displays a live video feed from the webcam and handles
    user interactions including image capture via space bar.
    """

    def __init__(
        self,
        webcam_service: IWebcamService,
        capture_service: CaptureService,
        visual_feedback: IVisualFeedback,
        file_monitor_service: Optional[IFileMonitorService] = None,
        comfyui_service: Optional[IComfyUIService] = None,
        orchestrator: Optional[ProcessingOrchestrator] = None
    ):
        """Initialize the main window.

        Args:
            webcam_service: Service for webcam video capture
            capture_service: Service for capturing and saving images
            visual_feedback: Service for visual feedback display
            file_monitor_service: Optional service for folder monitoring
            comfyui_service: Optional service for ComfyUI API
            orchestrator: Optional processing orchestrator for User Story 2
        """
        self._webcam_service = webcam_service
        self._capture_service = capture_service
        self._visual_feedback = visual_feedback
        self._file_monitor_service = file_monitor_service
        self._comfyui_service = comfyui_service
        self._orchestrator = orchestrator

        self._root = tk.Tk()
        self._root.title("Webcam to ComfyUI")
        self._root.geometry("1280x720")
        self._root.minsize(640, 480)

        # Create main frame
        self._main_frame = ttk.Frame(self._root, padding="10")
        self._main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)
        self._main_frame.columnconfigure(0, weight=1)
        self._main_frame.rowconfigure(0, weight=1)

        # Video feed frame
        self._video_frame = ttk.LabelFrame(
            self._main_frame, text="Video Feed", padding="5"
        )
        self._video_frame.grid(row=0, column=0, sticky="nsew")
        self._video_frame.columnconfigure(0, weight=1)
        self._video_frame.rowconfigure(0, weight=1)

        # Video label for displaying frames
        self._video_label = ttk.Label(self._video_frame)
        self._video_label.grid(row=0, column=0, sticky="nsew")

        # Status frame
        self._status_frame = ttk.Frame(self._main_frame, padding="5")
        self._status_frame.grid(row=1, column=0, sticky="ew")

        # Status label
        self._status_label = ttk.Label(
            self._status_frame, text="Status: Ready", foreground="green"
        )
        self._status_label.grid(row=0, column=0, sticky="w")

        # Controls frame
        self._controls_frame = ttk.Frame(self._main_frame, padding="5")
        self._controls_frame.grid(row=2, column=0, sticky="ew")

        # Capture button
        self._capture_button = ttk.Button(
            self._controls_frame, text="Capture Image", command=self._on_capture
        )
        self._capture_button.grid(row=0, column=0, padx=5)

        # Settings button
        self._settings_button = ttk.Button(
            self._controls_frame, text="Settings", command=self._on_settings
        )
        self._settings_button.grid(row=0, column=1, padx=5)

        # Quit button
        self._quit_button = ttk.Button(
            self._controls_frame, text="Quit", command=self._on_quit
        )
        self._quit_button.grid(row=0, column=2, padx=5)

        # Feedback indicator
        self._feedback_label = ttk.Label(
            self._status_frame, text="", foreground="blue"
        )
        self._feedback_label.grid(row=0, column=1, padx=10)

        # Video capture thread
        self._video_thread: Optional[threading.Thread] = None
        self._running = False

        # Bind space bar for capture
        self._root.bind('<space>', self._on_space_bar)

        # Handle window close
        self._root.protocol("WM_DELETE_WINDOW", self._on_quit)

    def _on_space_bar(self, event: tk.Event) -> None:
        """Handle space bar press for capture."""
        self._on_capture()

    def _on_capture(self) -> None:
        """Handle capture button press."""
        try:
            self._status_label.config(text="Status: Capturing...", foreground="orange")
            self._capture_button.config(state=tk.DISABLED)

            # Capture and save image
            image_capture = self._capture_service.capture()

            self._status_label.config(
                text=f"Status: Captured {image_capture.filepath}", foreground="green"
            )

        except Exception as e:
            self._status_label.config(
                text=f"Status: Error - {str(e)}", foreground="red"
            )
            messagebox.showerror("Capture Error", str(e))
        finally:
            self._capture_button.config(state=tk.NORMAL)

    def _on_settings(self) -> None:
        """Handle settings button press."""
        try:
            # Create settings service
            settings_service = SettingsService()

            # Create and show settings dialog
            dialog = SettingsDialog(
                self._root,
                settings_service,
                self._comfyui_service,
            )

            # Show dialog and get result
            new_settings, settings_changed = dialog.show()

            if settings_changed and new_settings:
                # Apply new settings
                self._apply_settings(new_settings)

        except Exception as e:
            messagebox.showerror("Settings Error", f"Failed to open settings: {str(e)}")

    def _apply_settings(self, settings) -> None:
        """Apply new settings to the application.

        Args:
            settings: New ApplicationSettings instance
        """
        # Update capture service output folder
        self._capture_service._output_folder = settings.output_folder

        # Update ComfyUI service endpoint and timeout if available
        if self._comfyui_service:
            self._comfyui_service._endpoint = settings.comfyui_endpoint.rstrip('/')
            self._comfyui_service._timeout = settings.api_timeout

        # Update orchestrator if available
        if self._orchestrator:
            self._orchestrator.update_settings(settings)

        # Update status label
        self._status_label.config(
            text=f"Status: Settings applied - {settings.output_folder}",
            foreground="green"
        )

    def _on_quit(self) -> None:
        """Handle quit button press."""
        self.stop()
        self._root.destroy()

    def _update_video_feed(self) -> None:
        """Update the video feed with the current frame."""
        if not self._running:
            return

        try:
            if self._webcam_service.is_running():
                # Capture frame for display (not saved)
                frame_data = self._webcam_service.capture_frame()

                # Convert to PIL Image for display
                import numpy as np
                frame = np.frombuffer(frame_data, dtype=np.uint8)
                frame = frame.reshape((1080, 1920, 3))

                # Convert BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert to PhotoImage
                pil_image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image=pil_image)

                # Update label
                self._video_label.config(image=photo)
                self._video_label.image = photo  # Keep reference

        except Exception:
            # Log error but continue trying
            pass

        # Schedule next frame update
        if self._running:
            self._root.after(33, self._update_video_feed)  # ~30 FPS

    def _show_feedback(self, feedback_type: str) -> None:
        """Show visual feedback for an operation.

        Args:
            feedback_type: Type of feedback ('capture', 'processing', etc.)
        """
        feedback_messages = {
            'capture': "Capturing...",
            'processing': "Processing...",
            'completion': "Processing complete!",
            'error': "Error occurred",
        }

        message = feedback_messages.get(feedback_type, "")
        self._feedback_label.config(text=message)

        # Clear feedback after 2 seconds
        self._root.after(2000, self._feedback_label.config, {'text': ''})

    def start(self) -> None:
        """Start the main window and video feed."""
        try:
            # Start webcam
            self._webcam_service.start()

            # Start video feed update loop
            self._running = True
            self._update_video_feed()

            # Start orchestrator if available (User Story 2)
            if self._orchestrator is not None:
                self._orchestrator.start()
                self._update_status_label()

            # Start main loop
            self._root.mainloop()

        except Exception as e:
            error_msg = f"Failed to start application: {str(e)}"
            messagebox.showerror("Startup Error", error_msg)
            raise

    def stop(self) -> None:
        """Stop the main window and release resources."""
        self._running = False

        try:
            # Stop orchestrator if running
            if self._orchestrator is not None and self._orchestrator.is_running():
                self._orchestrator.stop()

            # Stop webcam
            if self._webcam_service.is_running():
                self._webcam_service.stop()

        except Exception:
            pass

    def set_orchestrator(self, orchestrator: ProcessingOrchestrator) -> None:
        """Set the processing orchestrator for User Story 2 integration.

        Args:
            orchestrator: The processing orchestrator instance
        """
        self._orchestrator = orchestrator

    def _update_status_label(self) -> None:
        """Update the status label with processing information."""
        if self._orchestrator is not None:
            status = self._orchestrator.get_status()
            state = status.state
            queue_size = status.queue_size

            if state == 'processing':
                self._status_label.config(
                    text=f"Status: Processing (Queue: {queue_size})",
                    foreground="orange"
                )
            elif state == 'completed':
                self._status_label.config(
                    text="Status: Processing complete",
                    foreground="green"
                )
            elif state == 'error':
                self._status_label.config(
                    text=f"Status: Error - {status.error_message}",
                    foreground="red"
                )
            else:
                self._status_label.config(
                    text=f"Status: Ready (Queue: {queue_size})",
                    foreground="green"
                )
