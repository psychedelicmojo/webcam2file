"""Main window UI for the Webcam-to-ComfyUI Desktop Application."""

import logging
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

import cv2
from PIL import Image, ImageTk

from src.lib.error_manager import ErrorManager
from src.services.capture_service import CaptureService
from src.services.comfyui_service import IComfyUIService
from src.services.file_monitor_service import IFileMonitorService
from src.services.processing_orchestrator import ProcessingOrchestrator
from src.services.settings_service import SettingsService
from src.services.visual_feedback import IVisualFeedback
from src.services.webcam_service import IWebcamService
from src.ui.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


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
        orchestrator: Optional[ProcessingOrchestrator] = None,
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
        self._error_manager = ErrorManager()

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
        self._main_frame.columnconfigure(1, weight=0)  # Sidebar column
        self._main_frame.rowconfigure(0, weight=1)

        # Video feed frame (left side)
        self._video_frame = ttk.LabelFrame(
            self._main_frame, text="Video Feed", padding="5"
        )
        self._video_frame.grid(row=0, column=0, sticky="nsew")
        self._video_frame.columnconfigure(0, weight=1)
        self._video_frame.rowconfigure(0, weight=1)

        # Video label for displaying frames
        self._video_label = ttk.Label(self._video_frame)
        self._video_label.grid(row=0, column=0, sticky="nsew")
        
        # Placeholder for the current photo image (created later when window is visible)
        self._current_photo = None
        
        # Video display settings
        self._display_width = 1280
        self._display_height = 720

        # Sidebar frame (right side)
        self._sidebar_frame = ttk.Frame(self._main_frame, padding="5")
        self._sidebar_frame.grid(row=0, column=1, sticky="ns", padx=(10, 0))
        self._sidebar_frame.rowconfigure(0, weight=1)

        # Style selection section
        style_frame = ttk.LabelFrame(self._sidebar_frame, text="Style Selection", padding="5")
        style_frame.grid(row=0, column=0, sticky="nsew")

        # Style dropdown
        self._style_var = tk.StringVar()
        self._style_dropdown = ttk.Combobox(
            style_frame,
            textvariable=self._style_var,
            state="readonly",
            width=30
        )
        self._style_dropdown.grid(row=0, column=0, sticky="ew", pady=5)
        self._style_dropdown.bind("<<ComboboxSelected>>", self._on_style_change)

        # Style info label
        self._style_info_label = ttk.Label(
            style_frame,
            text="Select an art style to apply",
            wraplength=200,
            foreground="gray"
        )
        self._style_info_label.grid(row=1, column=0, sticky="ew", pady=(5, 0))

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
        self._feedback_label = ttk.Label(self._status_frame, text="", foreground="blue")
        self._feedback_label.grid(row=0, column=1, padx=10)

        # Video capture thread
        self._video_thread: Optional[threading.Thread] = None
        self._running = False
        self._video_feed_after_id: Optional[str] = None

        # Bind space bar for capture (prevent default button behavior)
        self._root.bind("<space>", lambda e: (self._on_space_bar(e), "break"))

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
            error_info = self._error_manager.handle_error(e)
            self._status_label.config(
                text=f"Status: Error - {error_info['user_message']}", foreground="red"
            )
            self._show_error_dialog(
                title="Capture Error",
                message=error_info["user_message"],
                recovery_action=error_info["recovery_action"],
            )
            logger.error(f"Capture error: {error_info['original_message']}")
        finally:
            self._capture_button.config(state=tk.NORMAL)

    def _show_error_dialog(
        self, title: str, message: str, recovery_action: str
    ) -> None:
        """Show an error dialog with user-friendly message and recovery action.

        Args:
            title: Dialog title
            message: Error message to display
            recovery_action: Suggested recovery action
        """
        # Create a custom error dialog
        dialog = tk.Toplevel(self._root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.transient(self._root)
        dialog.grab_set()

        # Icon frame
        icon_frame = ttk.Frame(dialog, padding="10")
        icon_frame.pack(fill="x")

        icon_label = ttk.Label(icon_frame, text="⚠️", font=("Segoe UI", 48))
        icon_label.pack()

        # Message frame
        message_frame = ttk.Frame(dialog, padding="10")
        message_frame.pack(fill="both", expand=True)

        message_label = ttk.Label(
            message_frame, text=message, wraplength=350, font=("Segoe UI", 10)
        )
        message_label.pack(pady=(0, 10))

        # Recovery action frame
        recovery_frame = ttk.Frame(message_frame, padding="5")
        recovery_frame.pack(fill="x")

        recovery_label = ttk.Label(
            recovery_frame,
            text=f"Recovery: {recovery_action}",
            wraplength=350,
            foreground="orange",
            font=("Segoe UI", 9, "italic"),
        )
        recovery_label.pack()

        # Button frame
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.pack(fill="x")

        ok_button = ttk.Button(button_frame, text="OK", command=dialog.destroy)
        ok_button.pack(side="right", padx=5)

        # Center dialog on parent
        dialog.geometry(f"+{self._root.winfo_x() + 100}+{self._root.winfo_y() + 100}")

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
            error_info = self._error_manager.handle_error(e)
            self._show_error_dialog(
                title="Settings Error",
                message=f"Failed to open settings: {error_info['user_message']}",
                recovery_action=error_info["recovery_action"],
            )
            logger.error(f"Settings error: {error_info['original_message']}")

    def _apply_settings(self, settings) -> None:
        """Apply new settings to the application.

        Args:
            settings: New ApplicationSettings instance
        """
        # Update capture service output folder
        self._capture_service._output_folder = settings.output_folder

        # Update ComfyUI service endpoint and timeout if available
        if self._comfyui_service:
            self._comfyui_service.set_endpoint(settings.comfyui_endpoint.rstrip("/"))
            self._comfyui_service.set_timeout(settings.api_timeout)

        # Update orchestrator if available
        if self._orchestrator:
            self._orchestrator.update_settings(settings)

        # Update style dropdown with loaded styles
        if hasattr(settings, 'art_styles') and settings.art_styles:
            self._style_dropdown['values'] = settings.art_styles
            if settings.art_styles:
                self._style_var.set(settings.art_styles[0])

        # Update status label
        self._status_label.config(
            text=f"Status: Settings applied - {settings.output_folder}",
            foreground="green",
        )

    def _on_style_change(self, event=None) -> None:
        """Handle style selection change.

        Args:
            event: The event object (optional)
        """
        selected_style = self._style_var.get().strip()
        if selected_style:
            self._status_label.config(
                text=f"Status: Style selected - {selected_style}",
                foreground="blue",
            )
            # Clear status after 3 seconds
            self._root.after(3000, lambda: self._status_label.config(
                text=f"Status: Ready", foreground="green"
            ))

    def _on_quit(self) -> None:
        """Handle quit button press."""
        self.stop()
        self._root.destroy()

    def _update_video_feed(self) -> None:
        """Update the video feed with the current frame."""
        if not self._running:
            return

        try:
            # Check if window still exists before updating
            if not self._root.winfo_exists():
                return

            if self._webcam_service.is_running():
                # Capture frame for display (not saved)
                frame_data = self._webcam_service.capture_frame()

                # Debug: Check if frame data is valid
                if not frame_data or len(frame_data) == 0:
                    logger.error("Empty frame data received")
                    self._schedule_next_frame()
                    return

                # Convert to PIL Image for display
                import numpy as np
                from PIL import Image

                # Decode JPEG to get actual frame dimensions
                # cv2.imdecode expects a numpy array, not bytes
                frame_array = np.frombuffer(frame_data, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
              
                if frame is None:
                    logger.error("Failed to decode frame")
                    self._schedule_next_frame()
                    return

                # Convert BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Get original frame dimensions
                original_height, original_width = frame.shape[:2]
                
                # Calculate display area size (accounting for padding)
                display_width = self._video_frame.winfo_width() - 20 if self._video_frame.winfo_width() > 1 else self._display_width
                display_height = self._video_frame.winfo_height() - 60 if self._video_frame.winfo_height() > 1 else self._display_height
                
                # Calculate aspect ratio
                frame_aspect = original_width / original_height
                display_aspect = display_width / display_height
                
                # Determine scaled dimensions while maintaining aspect ratio
                if frame_aspect > display_aspect:
                    # Width is the limiting factor
                    scaled_width = display_width
                    scaled_height = int(display_width / frame_aspect)
                else:
                    # Height is the limiting factor
                    scaled_height = display_height
                    scaled_width = int(display_height * frame_aspect)
                
                # Ensure minimum display size
                scaled_width = max(320, scaled_width)
                scaled_height = max(240, scaled_height)

                # Resize frame to fit display area
                pil_image = Image.fromarray(frame)
                resized_image = pil_image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(image=resized_image)

                # Update label - check if widget still exists
                try:
                    self._video_label.config(image=photo)
                    # Store reference in the instance variable to prevent garbage collection
                    self._current_photo = photo
                except tk.TclError:
                    # Widget may have been destroyed
                    pass

        except Exception as e:
            # Log error but continue trying
            logger.error(f"Video feed update error: {e}")
            import traceback
            logger.error(f"Video feed traceback: {traceback.format_exc()}")

        # Schedule next frame update
        if self._running:
            self._schedule_next_frame()

    def _schedule_next_frame(self) -> None:
        """Schedule the next video frame update, canceling any pending update."""
        if not self._running:
            return
        # Cancel any pending update to avoid queue buildup
        if self._video_feed_after_id is not None:
            try:
                self._root.after_cancel(self._video_feed_after_id)
            except tk.TclError:
                # Window may be closing
                return
        # Schedule new update
        try:
            self._video_feed_after_id = self._root.after(33, self._update_video_feed)
        except tk.TclError:
            # Window may be closing
            pass

    def _show_feedback(self, feedback_type: str) -> None:
        """Show visual feedback for an operation.

        Args:
            feedback_type: Type of feedback ('capture', 'processing', etc.)
        """
        feedback_messages = {
            "capture": "Capturing...",
            "processing": "Processing...",
            "completion": "Processing complete!",
            "error": "Error occurred",
        }

        message = feedback_messages.get(feedback_type, "")
        self._feedback_label.config(text=message)

        # Clear feedback after 2 seconds
        self._root.after(2000, self._feedback_label.config, {"text": ""})

    def start(self) -> None:
        """Start the main window and video feed."""
        try:
            # Start webcam
            self._webcam_service.start()

            # Start orchestrator if available (User Story 2)
            if self._orchestrator is not None:
                self._orchestrator.start()
                self._update_status_label()

            # Show the window and process events
            self._root.deiconify()
            self._root.update()

            # Start main loop first
            self._running = True
        
            # Schedule video feed update after window is visible
            # Use after_idle to ensure all pending events are processed first
            self._root.after_idle(self._update_video_feed)
            
            # Start main loop
            self._root.mainloop()

        except Exception as e:
            error_info = self._error_manager.handle_error(e)
            error_msg = f"Failed to start application: {error_info['user_message']}"
            messagebox.showerror("Startup Error", error_msg)
            logger.error(f"Startup error: {error_info['original_message']}")
            raise

    def _video_feed_loop(self) -> None:
        """Run the video feed update loop in a separate thread."""
        while self._running:
            try:
                self._update_video_feed()
            except Exception as e:
                logger.debug(f"Video feed loop error: {e}")
            # Sleep to avoid busy-waiting
            import time
            time.sleep(0.033)  # ~30 FPS

    def stop(self) -> None:
        """Stop the main window and release resources."""
        self._running = False

        try:
            # Cancel any pending video feed updates
            if self._video_feed_after_id is not None:
                try:
                    self._root.after_cancel(self._video_feed_after_id)
                except tk.TclError:
                    pass
                self._video_feed_after_id = None

            # Stop orchestrator if running
            if self._orchestrator is not None and self._orchestrator.is_running():
                self._orchestrator.stop()

            # Stop webcam
            if self._webcam_service.is_running():
                self._webcam_service.stop()

        except Exception as e:
            logger.debug(f"Error during shutdown: {e}")
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

            if state == "processing":
                self._status_label.config(
                    text=f"Status: Processing (Queue: {queue_size})",
                    foreground="orange",
                )
            elif state == "completed":
                self._status_label.config(
                    text="Status: Processing complete", foreground="green"
                )
            elif state == "error":
                self._status_label.config(
                    text=f"Status: Error - {status.error_message}", foreground="red"
                )
            else:
                self._status_label.config(
                    text=f"Status: Ready (Queue: {queue_size})", foreground="green"
                )
