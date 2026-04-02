"""Google Apps Script email service implementation.

Sends images by POSTing base64-encoded image data to a Google Apps Script
web app, which uploads to Google Drive and sends via Gmail.

Expected Apps Script doPost payload:
  {
    "email": "recipient@example.com",
    "filename": "Creative_School_AI_Photobooth_....jpg",
    "imageData": "<base64-encoded JPEG>"
  }
"""

import base64
import logging
from pathlib import Path

import requests

from src.services.email_service import EmailSendError, IEmailService

logger = logging.getLogger(__name__)


class GoogleAppsScriptEmailService(IEmailService):
    """Sends images via a Google Apps Script web app endpoint."""

    def __init__(self, apps_script_url: str, timeout: int = 30) -> None:
        """Initialize the email service.

        Args:
            apps_script_url: Deployed Google Apps Script web app URL.
            timeout: HTTP request timeout in seconds.
        """
        self._url = apps_script_url
        self._timeout = timeout

    def send_image(self, image_path: str, recipient_email: str) -> None:
        """Send an image to a recipient via Google Apps Script.

        Args:
            image_path: Path to the JPEG image to send.
            recipient_email: Recipient email address.

        Raises:
            EmailSendError: If the URL is not configured, the file cannot be
                read, or the Apps Script request fails.
        """
        if not self._url:
            raise EmailSendError(
                "Apps Script URL is not configured. "
                "Please add it under Settings > Apps Script URL."
            )

        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
        except OSError as e:
            raise EmailSendError(f"Cannot read image file: {e}") from e

        payload = {
            "email": recipient_email,
            "filename": Path(image_path).name,
            "imageData": image_data,
        }

        try:
            response = requests.post(self._url, json=payload, timeout=self._timeout)
            response.raise_for_status()
            logger.info(f"Email sent to {recipient_email} for {Path(image_path).name}")
        except requests.exceptions.ConnectionError as e:
            raise EmailSendError(f"Cannot connect to Apps Script endpoint: {e}") from e
        except requests.exceptions.Timeout:
            raise EmailSendError("Request to Apps Script timed out.") from None
        except requests.exceptions.HTTPError as e:
            raise EmailSendError(f"Apps Script returned an error: {e}") from e
        except Exception as e:
            raise EmailSendError(f"Unexpected error sending email: {e}") from e

    def set_url(self, url: str) -> None:
        """Update the Apps Script endpoint URL.

        Args:
            url: New Apps Script web app URL.
        """
        self._url = url
