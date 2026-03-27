"""Unit tests for ErrorManager utility."""

from src.lib.error_manager import ErrorManager
from src.services.comfyui_service import APIConnectionError, APIError, TimeoutError
from src.services.file_monitor_service import FolderAccessError, FolderNotFoundError
from src.services.webcam_service import WebcamAccessError, WebcamNotFoundError


class TestErrorManagerUnit:
    """Unit tests for ErrorManager utility."""

    def setup_method(self):
        """Set up test fixtures."""
        self.error_manager = ErrorManager()

    def test_webcam_not_found(self):
        """Verify correct error message and recovery action for WebcamNotFoundError."""
        error = WebcamNotFoundError("No webcam detected")
        result = self.error_manager.handle_error(error)

        assert (
            result["user_message"]
            == "No webcam detected. Please connect a webcam and try again."
        )
        assert result["recovery_action"] == "Connect webcam"
        assert result["error_type"] == "WebcamNotFoundError"
        assert result["original_message"] == "No webcam detected"

    def test_webcam_access_error(self):
        """Verify correct error message and recovery action for WebcamAccessError."""
        error = WebcamAccessError("Webcam access denied")
        result = self.error_manager.handle_error(error)

        assert (
            result["user_message"]
            == "Cannot access webcam. Close other applications using the webcam and try again."
        )
        assert result["recovery_action"] == "Close other apps"
        assert result["error_type"] == "WebcamAccessError"
        assert result["original_message"] == "Webcam access denied"

    def test_folder_not_found(self):
        """Verify correct error message and recovery action for FolderNotFoundError."""
        error = FolderNotFoundError("Folder not found")
        result = self.error_manager.handle_error(error)

        assert (
            result["user_message"]
            == "Output folder not found. Please select a valid folder in settings."
        )
        assert result["recovery_action"] == "Select valid folder"
        assert result["error_type"] == "FolderNotFoundError"
        assert result["original_message"] == "Folder not found"

    def test_folder_access_error(self):
        """Verify correct error message and recovery action for FolderAccessError."""
        error = FolderAccessError("Folder access denied")
        result = self.error_manager.handle_error(error)

        assert (
            result["user_message"]
            == "Cannot access output folder. Check permissions and try again."
        )
        assert result["recovery_action"] == "Check permissions"
        assert result["error_type"] == "FolderAccessError"
        assert result["original_message"] == "Folder access denied"

    def test_api_connection_error(self):
        """Verify correct error message and recovery action for APIConnectionError."""
        error = APIConnectionError("Connection failed")
        result = self.error_manager.handle_error(error)

        assert (
            result["user_message"]
            == "Cannot connect to ComfyUI. Make sure ComfyUI is running and try again."
        )
        assert result["recovery_action"] == "Start ComfyUI"
        assert result["error_type"] == "APIConnectionError"
        assert result["original_message"] == "Connection failed"

    def test_api_error(self):
        """Verify correct error message and recovery action for APIError."""
        error = APIError("ComfyUI returned error")
        result = self.error_manager.handle_error(error)

        assert (
            result["user_message"]
            == "ComfyUI returned an error. Check the workflow configuration and try again."
        )
        assert result["recovery_action"] == "Check workflow"
        assert result["error_type"] == "APIError"
        assert result["original_message"] == "ComfyUI returned error"

    def test_timeout_error(self):
        """Verify correct error message and recovery action for TimeoutError."""
        error = TimeoutError("Request timed out")
        result = self.error_manager.handle_error(error)

        assert (
            result["user_message"]
            == "Request to ComfyUI timed out. Check your network connection and try again."
        )
        assert result["recovery_action"] == "Retry request"
        assert result["error_type"] == "TimeoutError"
        assert result["original_message"] == "Request timed out"

    def test_get_recovery_action(self):
        """Verify get_recovery_action returns correct action for each error type."""
        assert (
            self.error_manager.get_recovery_action("WebcamNotFoundError")
            == "Connect webcam"
        )
        assert (
            self.error_manager.get_recovery_action("WebcamAccessError")
            == "Close other apps"
        )
        assert (
            self.error_manager.get_recovery_action("FolderNotFoundError")
            == "Select valid folder"
        )
        assert (
            self.error_manager.get_recovery_action("FolderAccessError")
            == "Check permissions"
        )
        assert (
            self.error_manager.get_recovery_action("APIConnectionError")
            == "Start ComfyUI"
        )
        assert self.error_manager.get_recovery_action("APIError") == "Check workflow"
        assert self.error_manager.get_recovery_action("TimeoutError") == "Retry request"

    def test_get_recovery_action_unknown_error(self):
        """Verify get_recovery_action returns default action for unknown error type."""
        assert (
            self.error_manager.get_recovery_action("UnknownError") == "Retry operation"
        )

    def test_is_recoverable(self):
        """Verify is_recoverable returns True for known error types."""
        assert self.error_manager.is_recoverable(WebcamNotFoundError("test")) is True
        assert self.error_manager.is_recoverable(WebcamAccessError("test")) is True
        assert self.error_manager.is_recoverable(FolderNotFoundError("test")) is True
        assert self.error_manager.is_recoverable(FolderAccessError("test")) is True
        assert self.error_manager.is_recoverable(APIConnectionError("test")) is True
        assert self.error_manager.is_recoverable(APIError("test")) is True
        assert self.error_manager.is_recoverable(TimeoutError("test")) is True

    def test_is_recoverable_unknown_error(self):
        """Verify is_recoverable returns False for unknown error types."""

        class CustomError(Exception):
            pass

        assert self.error_manager.is_recoverable(CustomError("test")) is False

    def test_handle_error_with_custom_message(self):
        """Verify handle_error uses custom user message when provided."""
        error = WebcamNotFoundError("No webcam detected")
        custom_message = "Custom error message"
        result = self.error_manager.handle_error(error, custom_message)

        assert result["user_message"] == custom_message
        assert result["recovery_action"] == "Connect webcam"

    def test_handle_error_unknown_error_type(self):
        """Verify handle_error uses default message for unknown error types."""

        class CustomError(Exception):
            pass

        error = CustomError("Unknown error")
        result = self.error_manager.handle_error(error)

        assert (
            result["user_message"] == "An unexpected error occurred. Please try again."
        )
        assert result["recovery_action"] == "Retry operation"
        assert result["error_type"] == "CustomError"
