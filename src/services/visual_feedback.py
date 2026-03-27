"""Service for providing visual feedback during operations."""

from abc import ABC, abstractmethod


class IVisualFeedback(ABC):
    """Interface for visual feedback display."""

    @abstractmethod
    def show_capture_feedback(self) -> None:
        """Show visual feedback for image capture."""
        pass

    @abstractmethod
    def show_processing_feedback(self) -> None:
        """Show visual feedback for processing start."""
        pass

    @abstractmethod
    def show_completion_feedback(self) -> None:
        """Show visual feedback for processing completion."""
        pass

    @abstractmethod
    def show_error_feedback(self, message: str) -> None:
        """Show visual feedback for errors.

        Args:
            message: Error message to display.
        """
        pass

    @abstractmethod
    def hide_feedback(self) -> None:
        """Hide all visual feedback."""
        pass


class VisualFeedback(IVisualFeedback):
    """Implementation of visual feedback service.

    Provides visual effects like subtle flash/border highlight
    around video feed area during operations.
    """

    def __init__(self) -> None:
        """Initialize the visual feedback service."""
        self._current_effect: str = ""

    def show_capture_feedback(self) -> None:
        """Show visual feedback for image capture."""
        self._current_effect = "capture"
        # Implementation will be provided by UI layer
        # This could trigger a CSS animation or visual effect

    def show_processing_feedback(self) -> None:
        """Show visual feedback for processing start."""
        self._current_effect = "processing"
        # Implementation will be provided by UI layer

    def show_completion_feedback(self) -> None:
        """Show visual feedback for processing completion."""
        self._current_effect = "completion"
        # Implementation will be provided by UI layer

    def show_error_feedback(self, message: str) -> None:
        """Show visual feedback for errors.

        Args:
            message: Error message to display.
        """
        self._current_effect = "error"
        # Implementation will be provided by UI layer

    def hide_feedback(self) -> None:
        """Hide all visual feedback."""
        self._current_effect = ""

    def get_current_effect(self) -> str:
        """Get the current visual effect.

        Returns:
            str: Current effect name or empty string if none.
        """
        return self._current_effect
