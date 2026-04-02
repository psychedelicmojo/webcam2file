"""Interface for ComfyUI API communication."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class APIConnectionError(Exception):
    """Raised when connection to ComfyUI fails."""

    pass


class APIError(Exception):
    """Raised when ComfyUI returns an error response."""

    pass


class TimeoutError(Exception):
    """Raised when request times out."""

    pass


class IComfyUIService(ABC):
    """Interface for ComfyUI API communication."""

    @abstractmethod
    def __init__(self, endpoint: str, timeout: int = 30) -> None:
        """Initialize the ComfyUI service.

        Args:
            endpoint: ComfyUI API endpoint URL.
            timeout: Request timeout in seconds.
        """
        pass

    @abstractmethod
    def trigger_workflow(
        self, workflow_json: Dict[str, Any], input_image_path: str
    ) -> str:
        """Trigger a ComfyUI workflow.

        Args:
            workflow_json: The ComfyUI workflow configuration.
            input_image_path: Path to the input image.

        Returns:
            str: The prompt ID for tracking the workflow.

        Raises:
            APIConnectionError: If connection to ComfyUI fails.
            APIError: If ComfyUI returns an error response.
            TimeoutError: If request times out.
        """
        pass

    @abstractmethod
    def check_status(self, prompt_id: str) -> Dict[str, Any]:
        """Check the status of a workflow.

        Args:
            prompt_id: The prompt ID returned from trigger_workflow().

        Returns:
            Dict[str, Any]: Workflow status information.

        Raises:
            APIConnectionError: If connection to ComfyUI fails.
            APIError: If ComfyUI returns an error response.
            TimeoutError: If request times out.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if ComfyUI API is accessible.

        Returns:
            bool: True if API is available, False otherwise.
        """
        pass

    @abstractmethod
    def upload_image(self, image_path: str) -> str:
        """Upload an image to ComfyUI's /upload/image endpoint.

        Args:
            image_path: Path to the local image file to upload.

        Returns:
            str: The filename as stored on the ComfyUI server.

        Raises:
            APIConnectionError: If connection to ComfyUI fails.
            APIError: If ComfyUI returns an error response.
            TimeoutError: If request times out.
        """
        pass

    @abstractmethod
    def wait_for_completion(
        self, prompt_id: str, timeout: Optional[int] = None, check_interval: float = 1.0
    ) -> Dict[str, Any]:
        """Wait for a workflow to complete.

        Args:
            prompt_id: The prompt ID to monitor.
            timeout: Maximum time to wait in seconds (default: service timeout).
            check_interval: Time between status checks in seconds (default: 1.0).

        Returns:
            Dict[str, Any]: Final workflow status information.

        Raises:
            TimeoutError: If workflow doesn't complete within timeout.
        """
        pass

    @abstractmethod
    def set_endpoint(self, endpoint: str) -> None:
        """Set the ComfyUI API endpoint.

        Args:
            endpoint: ComfyUI API endpoint URL.
        """
        pass

    @abstractmethod
    def set_timeout(self, timeout: int) -> None:
        """Set the request timeout in seconds.

        Args:
            timeout: Request timeout in seconds.
        """
        pass

    @abstractmethod
    def download_outputs(
        self, prompt_id: str, output_folder: str
    ) -> List[str]:
        """Download processed images from ComfyUI after workflow completion.

        Args:
            prompt_id: The prompt ID returned from trigger_workflow().
            output_folder: Local directory to save downloaded images.

        Returns:
            List[str]: List of paths to downloaded image files.

        Raises:
            APIConnectionError: If connection to ComfyUI fails.
            APIError: If ComfyUI returns an error response.
            TimeoutError: If request times out.
        """
        pass
