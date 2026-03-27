"""ProcessingStatus model for tracking processing state."""

from dataclasses import dataclass
from enum import Enum


class ProcessingState(Enum):
    """Enum for processing states."""

    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ProcessingStatus:
    """Represents the current state of image processing.

    Attributes:
        state: Current processing state (idle, processing, completed, error)
        current_image: Path to the image currently being processed (optional)
        error_message: Error message if state is error (optional)
        queue_size: Number of images waiting in queue
    """

    state: str = "idle"
    current_image: str = ""
    error_message: str = ""
    queue_size: int = 0

    VALID_STATES = {"idle", "processing", "completed", "error"}

    def __post_init__(self) -> None:
        """Validate the processing status after initialization."""
        self._validate_state()
        self._validate_state_consistency()

    def _validate_state(self) -> None:
        """Validate state is one of the allowed values."""
        if self.state not in self.VALID_STATES:
            raise ValueError(
                f"Invalid state: '{self.state}'. "
                f"Must be one of: {', '.join(self.VALID_STATES)}"
            )

    def _validate_state_consistency(self) -> None:
        """Validate state consistency with other fields."""
        if self.state == "processing" and not self.current_image:
            raise ValueError("State is 'processing' but current_image is not set")
        if self.state == "error" and not self.error_message:
            raise ValueError("State is 'error' but error_message is not set")
        if self.state in ("completed", "idle") and self.current_image:
            # These states can have current_image set from previous processing
            pass
        if self.state == "idle" and self.error_message:
            # Error message should be cleared when state returns to idle
            pass

    def update_state(self, new_state: str, error_message: str = "") -> None:
        """Update the processing state with validation.

        Args:
            new_state: The new state value
            error_message: Error message if state is error

        Raises:
            ValueError: If the new state is invalid or inconsistent
        """
        if new_state not in self.VALID_STATES:
            raise ValueError(
                f"Invalid state: '{new_state}'. "
                f"Must be one of: {', '.join(self.VALID_STATES)}"
            )

        self.state = new_state

        if new_state == "processing":
            if not self.current_image:
                raise ValueError(
                    "Cannot set state to 'processing' without current_image"
                )
        elif new_state == "error":
            if not error_message:
                raise ValueError("Cannot set state to 'error' without error_message")
            self.error_message = error_message
        elif new_state in ("completed", "idle"):
            # Clear error message on completion/idle
            self.error_message = ""

    def to_dict(self) -> dict:
        """Convert the ProcessingStatus to a dictionary.

        Returns:
            Dictionary representation of the ProcessingStatus
        """
        return {
            "state": self.state,
            "current_image": self.current_image,
            "error_message": self.error_message,
            "queue_size": self.queue_size,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProcessingStatus":
        """Create a ProcessingStatus from a dictionary.

        Args:
            data: Dictionary with ProcessingStatus data

        Returns:
            New ProcessingStatus instance
        """
        return cls(
            state=data.get("state", "idle"),
            current_image=data.get("current_image", ""),
            error_message=data.get("error_message", ""),
            queue_size=data.get("queue_size", 0),
        )
