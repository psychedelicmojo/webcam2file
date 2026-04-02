"""Utility for handling errors with user-friendly messages."""

from typing import Dict, Optional


class ErrorManager:
    """Manages error handling with user-friendly messages and recovery actions.

    Provides consistent error handling across the application with
    appropriate messages and recovery actions for different error types.
    """

    # Error type definitions with user messages and recovery actions
    ERROR_DEFINITIONS: Dict[str, Dict[str, str]] = {
        "WebcamNotFoundError": {
            "user_message": "No webcam detected. Please connect a webcam and try again.",
            "recovery_action": "Connect webcam",
        },
        "WebcamAccessError": {
            "user_message": (
                "Cannot access webcam. Close other applications using the webcam"
                " and try again."
            ),
            "recovery_action": "Close other apps",
        },
        "FolderNotFoundError": {
            "user_message": "Output folder not found. Please select a valid folder in settings.",
            "recovery_action": "Select valid folder",
        },
        "FolderAccessError": {
            "user_message": "Cannot access output folder. Check permissions and try again.",
            "recovery_action": "Check permissions",
        },
        "APIConnectionError": {
            "user_message": (
                "Cannot connect to ComfyUI. Make sure ComfyUI is running and try again."
            ),
            "recovery_action": "Start ComfyUI",
        },
        "APIError": {
            "user_message": (
                "ComfyUI returned an error. Check the workflow configuration"
                " and try again."
            ),
            "recovery_action": "Check workflow",
        },
        "TimeoutError": {
            "user_message": (
                "Request to ComfyUI timed out. Check your network connection"
                " and try again."
            ),
            "recovery_action": "Retry request",
        },
    }

    def handle_error(
        self, error: Exception, user_message: Optional[str] = None
    ) -> Dict[str, str]:
        """Handle an error and return user-friendly information.

        Args:
            error: The exception that occurred.
            user_message: Optional custom user message.

        Returns:
            Dictionary with 'user_message' and 'recovery_action' keys.
        """
        error_type = type(error).__name__

        if error_type in self.ERROR_DEFINITIONS:
            definition = self.ERROR_DEFINITIONS[error_type]
            return {
                "user_message": user_message or definition["user_message"],
                "recovery_action": definition["recovery_action"],
                "error_type": error_type,
                "original_message": str(error),
            }

        # Default error handling for unknown error types
        return {
            "user_message": user_message
            or "An unexpected error occurred. Please try again.",
            "recovery_action": "Retry operation",
            "error_type": error_type,
            "original_message": str(error),
        }

    def get_recovery_action(self, error_type: str) -> str:
        """Get the recovery action for a specific error type.

        Args:
            error_type: The name of the error class.

        Returns:
            The recovery action string, or default if not found.
        """
        if error_type in self.ERROR_DEFINITIONS:
            return self.ERROR_DEFINITIONS[error_type]["recovery_action"]
        return "Retry operation"

    def is_recoverable(self, error: Exception) -> bool:
        """Check if an error is recoverable.

        Args:
            error: The exception to check.

        Returns:
            True if the error is recoverable, False otherwise.
        """
        error_type = type(error).__name__
        return error_type in self.ERROR_DEFINITIONS
