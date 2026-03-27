"""Implementation of IWebcamService using OpenCV for video capture."""

from typing import Optional

import cv2

from src.services.webcam_service import (
    CaptureError,
    IWebcamService,
    WebcamAccessError,
    WebcamNotFoundError,
    WebcamNotStartedError,
)


class WebcamServiceImpl(IWebcamService):
    """Implementation of IWebcamService using OpenCV for video capture.

    This service provides HD video capture (1920x1080) from the default webcam.
    It handles webcam initialization, frame capture, and proper resource cleanup.
    """

    def __init__(self, webcam_index: int = 0, width: int = 1920, height: int = 1080):
        """Initialize the webcam service.

        Args:
            webcam_index: The index of the webcam device (default: 0 for default webcam)
            width: The frame width in pixels (default: 1920 for HD)
            height: The frame height in pixels (default: 1080 for HD)
        """
        self._webcam_index = webcam_index
        self._width = width
        self._height = height
        self._cap: Optional[cv2.VideoCapture] = None
        self._running = False

    def start(self) -> None:
        """Start the webcam video feed.

        Initializes the webcam with the configured resolution and starts
        capturing video frames.

        Raises:
            WebcamNotFoundError: If no webcam is available at the specified index
            WebcamAccessError: If webcam access is denied (e.g., in use by another app)
        """
        try:
            # Initialize video capture
            self._cap = cv2.VideoCapture(self._webcam_index)

            # Check if webcam opened successfully
            if not self._cap.isOpened():
                raise WebcamNotFoundError(
                    f"Failed to open webcam at index {self._webcam_index}. "
                    "Please connect a webcam and ensure no other application is using it."
                )

            # Set HD resolution
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)

            # Try to set a reasonable frame rate
            self._cap.set(cv2.CAP_PROP_FPS, 30)

            self._running = True

        except cv2.error as e:
            raise WebcamAccessError(
                f"Cannot access webcam. Close other applications using the webcam: {str(e)}"
            )

    def stop(self) -> None:
        """Stop the webcam video feed and release resources.

        Releases the webcam capture object and frees system resources.
        """
        if not self._running:
            raise WebcamNotStartedError("Webcam is not started")

        if self._cap is not None:
            self._cap.release()
            self._cap = None

        self._running = False

    def capture_frame(self) -> bytes:
        """Capture the current video frame.

        Reads the current frame from the webcam and encodes it as JPEG.

        Returns:
            bytes: JPEG-encoded image data.

        Raises:
            WebcamNotStartedError: If start() was not called before capture
            CaptureError: If frame capture fails
        """
        if not self._running:
            raise WebcamNotStartedError("Webcam is not started. Call start() first.")

        if self._cap is None:
            raise CaptureError("Video capture object is not initialized")

        try:
            # Read frame from webcam
            ret, frame = self._cap.read()

            if not ret:
                raise CaptureError("Failed to capture frame from webcam")

            # Encode frame as JPEG
            # OpenCV uses BGR, but JPEG typically expects RGB
            # However, OpenCV's imencode handles BGR correctly for JPEG
            success, buffer = cv2.imencode(".jpg", frame)

            if not success:
                raise CaptureError("Failed to encode frame as JPEG")

            return buffer.tobytes()

        except cv2.error as e:
            raise CaptureError(f"OpenCV error during frame capture: {str(e)}")

    def is_running(self) -> bool:
        """Check if the webcam is currently running.

        Returns:
            bool: True if the webcam is running and capturing frames, False otherwise.
        """
        return self._running and self._cap is not None

    @property
    def resolution(self) -> tuple:
        """Get the current resolution settings.

        Returns:
            tuple: (width, height) of the configured resolution
        """
        return (self._width, self._height)

    @staticmethod
    def list_available_webcams(max_devices: int = 10) -> list:
        """List available webcam devices.

        Args:
            max_devices: Maximum number of devices to check (default: 10)

        Returns:
            list: List of tuples (index, name) for available webcams
        """
        available = []
        for i in range(max_devices):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Try to get camera name (may not work on all platforms)
                    name = f"Webcam {i}"
                    # Try to read a frame to verify it works
                    ret, _ = cap.read()
                    if ret:
                        available.append((i, name))
                    cap.release()
            except cv2.error:
                pass
        return available
