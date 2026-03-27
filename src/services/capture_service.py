"""Service for capturing images from webcam and saving to file system."""

from pathlib import Path

from src.lib.error_manager import ErrorManager
from src.models.image_capture import ImageCapture
from src.services.visual_feedback import IVisualFeedback
from src.services.webcam_service import (
    CaptureError,
    IWebcamService,
    WebcamAccessError,
    WebcamNotFoundError,
    WebcamNotStartedError,
)


class CaptureService:
    """Service for capturing images from webcam and saving to file system."""

    def __init__(
        self,
        webcam_service: IWebcamService,
        visual_feedback: IVisualFeedback,
        output_folder: str,
    ):
        """Initialize the capture service.

        Args:
            webcam_service: Service for webcam video capture
            visual_feedback: Service for visual feedback display
            output_folder: Directory where captured images are saved
        """
        self._webcam_service = webcam_service
        self._visual_feedback = visual_feedback
        self._output_folder = output_folder
        self._error_manager = ErrorManager()

    def capture(self) -> ImageCapture:
        """Capture a frame from the webcam and save it to the output folder.

        Returns:
            ImageCapture: The captured image information

        Raises:
            WebcamNotFoundError: If no webcam is available
            WebcamAccessError: If webcam access is denied
            WebcamNotStartedError: If webcam is not running
            CaptureError: If frame capture fails
            IOError: If file save fails
        """
        # Show capture feedback
        self._visual_feedback.show_capture_feedback()

        try:
            # Capture frame from webcam
            frame_data = self._webcam_service.capture_frame()

            # Generate unique filename
            from src.lib.file_utils import FileUtils

            filename = FileUtils.generate_unique_filename(
                prefix="capture", suffix=".jpg"
            )
            filepath = Path(self._output_folder) / filename

            # Save frame to file
            with open(filepath, "wb") as f:
                f.write(frame_data)

            # Get file size
            filesize = filepath.stat().st_size

            # Create ImageCapture object
            image_capture = ImageCapture(
                timestamp=filename.replace(".jpg", "").replace("capture_", ""),
                filepath=str(filepath),
                filesize=filesize,
                output_folder=self._output_folder,
                status="pending",
            )

            # Hide feedback
            self._visual_feedback.hide_feedback()

            return image_capture

        except WebcamNotFoundError as e:
            self._visual_feedback.hide_feedback()
            error_info = self._error_manager.handle_error(
                e, "No webcam detected. Please connect a webcam and try again."
            )
            raise CaptureError(error_info["user_message"]) from e
        except WebcamAccessError as e:
            self._visual_feedback.hide_feedback()
            error_info = self._error_manager.handle_error(
                e,
                "Cannot access webcam. Close other applications using the webcam and try again.",
            )
            raise CaptureError(error_info["user_message"]) from e
        except WebcamNotStartedError:
            self._visual_feedback.hide_feedback()
            raise
        except Exception as e:
            self._visual_feedback.hide_feedback()
            error_info = self._error_manager.handle_error(e, "Failed to capture frame.")
            raise CaptureError(error_info["user_message"]) from e
