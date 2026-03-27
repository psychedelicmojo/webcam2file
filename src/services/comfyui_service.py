"""Interface for ComfyUI API communication."""

from abc import ABC, abstractmethod
from typing import Any, Dict


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
