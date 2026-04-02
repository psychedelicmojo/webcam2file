"""Implementation of IComfyUIService using requests for ComfyUI API communication."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        self._endpoint = endpoint.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()

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
        try:
            # Prepare the payload with the workflow
            # ComfyUI API expects {"prompt": workflow_json}
            payload = {"prompt": workflow_json}

            # Make the API call
            response = self._session.post(
                f"{self._endpoint}/prompt", json=payload, timeout=self._timeout
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
            Dict[str, Any]: Workflow status information. Returns a dict with
                "completed": True if the prompt is found in history (workflow done),
                "completed": False if the prompt is not in history (still pending).

        Raises:
            APIConnectionError: If connection to ComfyUI fails.
            APIError: If ComfyUI returns an error response.
            TimeoutError: If request times out.
        """
        try:
            # Check workflow history
            response = self._session.get(
                f"{self._endpoint}/history/{prompt_id}", timeout=self._timeout
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            result = response.json()

            if prompt_id in result:
                # Prompt found in history - workflow is complete
                return {
                    "prompt_id": prompt_id,
                    "completed": True,
                    "history": result[prompt_id],
                }

            # Prompt not found in history - still pending
            return {"prompt_id": prompt_id, "completed": False}

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
                f"{self._endpoint}/system_stats", timeout=self._timeout
            )
            return response.status_code == 200
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return False

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
        try:
            # Read the image file
            with open(image_path, "rb") as f:
                files = {"image": (os.path.basename(image_path), f, "image/*")}

                # Make the upload request
                response = self._session.post(
                    f"{self._endpoint}/upload/image",
                    files=files,
                    timeout=self._timeout,
                )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            result = response.json()

            # ComfyUI returns {"name": "filename.jpg"}
            if "name" in result:
                return result["name"]

            # Alternative response format
            if isinstance(result, dict) and "name" in result:
                return result["name"]

            raise APIError("Unexpected response format from upload endpoint")

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
                f"ComfyUI returned an error (HTTP {status_code}) during image upload. "
                "Check the workflow configuration and try again."
            ) from e

    def wait_for_completion(
        self, prompt_id: str, timeout: Optional[int] = None, check_interval: float = 1.0
    ) -> Dict[str, Any]:
        """Wait for a workflow to complete.

        Args:
            prompt_id: The prompt ID to monitor.
            timeout: Maximum time to wait in seconds (default: service timeout).
            check_interval: Time between status checks in seconds (default: 1.0).

        Returns:
            Dict[str, Any]: Final workflow status information containing the
                history object under the "history" key.

        Raises:
            TimeoutError: If workflow doesn't complete within timeout.
        """
        start_time = time.time()
        max_timeout = timeout or self._timeout

        while time.time() - start_time < max_timeout:
            status = self.check_status(prompt_id)

            # Check if workflow is complete (prompt found in history)
            if status.get("completed"):
                return status

            # Wait before next check
            time.sleep(check_interval)

        raise TimeoutError(
            f"Workflow {prompt_id} did not complete within {max_timeout} seconds."
        )

    def download_outputs(self, prompt_id: str, output_folder: str) -> List[str]:
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
        downloaded_files: List[str] = []

        try:
            # Get workflow history to find output files
            response = self._session.get(
                f"{self._endpoint}/history/{prompt_id}", timeout=self._timeout
            )
            response.raise_for_status()
            result = response.json()

            if prompt_id not in result:
                return downloaded_files

            prompt_history = result[prompt_id]
            outputs = prompt_history.get("outputs", {})

            # Process each node in the workflow output
            for _node_id, node_output in outputs.items():
                # Check for images in the output
                if "images" in node_output:
                    for image_info in node_output["images"]:
                        # ComfyUI returns image info with filename, type, etc.
                        filename = image_info.get("filename", "")
                        subfolder = image_info.get("subfolder", "")
                        image_type = image_info.get("type", "output")

                        # Skip temp images — these are PreviewImage node outputs,
                        # not the final SaveImage output. Downloading both causes
                        # duplicate files with identical content.
                        if image_type == "temp":
                            continue

                        # Build the URL to download the image
                        # ComfyUI /view endpoint supports: /view?filename=...&subfolder=...&type=...
                        params: Dict[str, str] = {
                            "filename": filename,
                            "type": image_type,
                        }
                        if subfolder:
                            params["subfolder"] = subfolder

                        # Download the image
                        image_response = self._session.get(
                            f"{self._endpoint}/view",
                            params=params,
                            timeout=self._timeout,
                        )
                        image_response.raise_for_status()

                        # Create output file path
                        output_path = Path(output_folder) / filename
                        # Ensure output folder exists
                        output_path.parent.mkdir(parents=True, exist_ok=True)

                        # Save the image
                        with open(output_path, "wb") as f:
                            f.write(image_response.content)

                        downloaded_files.append(str(output_path))

            return downloaded_files

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
                f"ComfyUI returned an error (HTTP {status_code}) during output download. "
                "Check the workflow configuration and try again."
            ) from e

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

    def set_endpoint(self, endpoint: str) -> None:
        """Set the ComfyUI API endpoint.

        Args:
            endpoint: ComfyUI API endpoint URL.
        """
        self._endpoint = endpoint.rstrip("/")

    def set_timeout(self, timeout: int) -> None:
        """Set the request timeout in seconds.

        Args:
            timeout: Request timeout in seconds.
        """
        self._timeout = timeout
