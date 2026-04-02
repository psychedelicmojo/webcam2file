"""Interface for sending images via email."""

from abc import ABC, abstractmethod


class EmailSendError(Exception):
    """Raised when sending an email fails."""

    pass


class IEmailService(ABC):
    """Interface for sending images via email."""

    @abstractmethod
    def send_image(self, image_path: str, recipient_email: str) -> None:
        """Send an image to a recipient email address.

        Args:
            image_path: Path to the image file to send.
            recipient_email: Email address of the recipient.

        Raises:
            EmailSendError: If sending fails.
        """
        pass

    @abstractmethod
    def set_url(self, url: str) -> None:
        """Update the Apps Script endpoint URL.

        Args:
            url: New Apps Script web app URL.
        """
        pass
