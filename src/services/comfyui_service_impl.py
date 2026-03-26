"""Implementation of IComfyUIService using requests for ComfyUI API communication."""

import time
from typing import Any, Dict, Optional

import requests

from src.services.comfyui_service import (
    APIConnectionError,
    APIError,
    IComfyUIService,
    TimeoutError,
)


class ComfyUIService(IComfyUIService):
    """Implementation of IComfyUIService using requests for ComfyUI API communication.
    
    This service provides methods to trigger ComfyUI workflows, check their status,
    and verify API availability. It handles timeouts and error responses gracefully.
    """

    def __init__(self, endpoint: str = "http://127.0.0.1:8188", timeout: int = 30):
        """Initialize the ComfyUI service.
        
        Args:
            endpoint: ComfyUI API endpoint URL (default: http://127.0.0.1:8188)
            timeout: Request timeout in seconds (default: 30)
        """
        self._endpoint = endpoint.rstrip('/')
        self._timeout = timeout
        self._session = requests.Session()

    def trigger_workflow(
        self,
        workflow_json: Dict[str, Any],
        input_image_path: str
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
        try:
            # Prepare the payload with the workflow and input image
            payload = {
                "prompt": workflow_json,
                "inputs": {
                    "image": input_image_path
                }
            }

            # Make the API call
            response = self._session.post(
                f"{self._endpoint}/prompt",
                json=payload,
                timeout=self._timeout
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            result = response.json()

            # Extract prompt ID from response
            # ComfyUI typically returns {"prompt_id": "some-uuid"}
            if "prompt_id" in result:
                return result["prompt_id"]

            # Alternative response format
            if isinstance(result, dict) and len(result) > 0:
                # Return the first key as prompt_id
                return list(result.keys())[0]

            raise APIError("Unexpected response format from ComfyUI API")

        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(
                f"Cannot connect to ComfyUI at {self._endpoint}. "
                "Make sure ComfyUI is running and try again."
            ) from e
        except requests.exceptions.Timeout as e:
            raise TimeoutError(
                f"Request to ComfyUI timed out after {self._timeout} seconds. "
                "Check your network connection and try again."
            ) from e
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            raise APIError(
                f"ComfyUI returned an error (HTTP {status_code}). "
                "Check the workflow configuration and try again."
            ) from e
        except ValueError as e:
            raise APIError(
                f"Failed to parse ComfyUI API response: {str(e)}. "
                "Check the workflow configuration and try again."
            ) from e

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
        try:
            # Check workflow history
            response = self._session.get(
                f"{self._endpoint}/history/{prompt_id}",
                timeout=self._timeout
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            result = response.json()

            if prompt_id in result:
                return result[prompt_id]

            # Return empty status if not found
            return {
                "prompt_id": prompt_id,
                "status": "pending",
                "progress": None
            }

        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(
                f"Cannot connect to ComfyUI at {self._endpoint}. "
                "Make sure ComfyUI is running and try again."
            ) from e
        except requests.exceptions.Timeout as e:
            raise TimeoutError(
                f"Request to ComfyUI timed out after {self._timeout} seconds. "
                "Check your network connection and try again."
            ) from e
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            raise APIError(
                f"ComfyUI returned an error (HTTP {status_code}). "
                "Check the workflow configuration and try again."
            ) from e

    def is_available(self) -> bool:
        """Check if ComfyUI API is accessible.
        
        Returns:
            bool: True if API is available, False otherwise.
        """
        try:
            # Try to get the server info or check if endpoint responds
            response = self._session.get(
                f"{self._endpoint}/system_stats",
                timeout=self._timeout
            )
            return response.status_code == 200
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return False

    @property
    def endpoint(self) -> str:
        """Get the ComfyUI API endpoint.
        
        Returns:
            str: The endpoint URL.
        """
        return self._endpoint

    @property
    def timeout(self) -> int:
        """Get the request timeout in seconds.
        
        Returns:
            int: The timeout value.
        """
        return self._timeout

    def wait_for_completion(
        self,
        prompt_id: str,
        timeout: Optional[int] = None,
        check_interval: float = 1.0
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
        start_time = time.time()
        max_timeout = timeout or self._timeout

        while time.time() - start_time < max_timeout:
            status = self.check_status(prompt_id)

            # Check if workflow is complete
            if status.get("status") == "completed":
                return status

            # Check for error
            if status.get("status") == "error":
                raise APIError(f"Workflow failed: {status.get('error', 'Unknown error')}")

            # Wait before next check
            time.sleep(check_interval)

        raise TimeoutError(
            f"Workflow {prompt_id} did not complete within {max_timeout} seconds."
        )
