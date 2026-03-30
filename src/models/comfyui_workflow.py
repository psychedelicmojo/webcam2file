"""ComfyUIWorkflow model for workflow configuration."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ComfyUIWorkflow:
    """Represents the art style processing configuration.

    Attributes:
        workflow_json: The ComfyUI workflow configuration
        input_image_path: Path to the input image for processing
        output_location: Directory where processed images are saved
        prompt_id: ComfyUI prompt ID returned from API (optional)
    """

    workflow_json: dict
    input_image_path: str
    output_location: str
    prompt_id: str = ""

    def __post_init__(self) -> None:
        """Validate the ComfyUI workflow after initialization."""
        self.validate()

    def validate(self) -> bool:
        """Validate the workflow configuration.

        Returns:
            True if the workflow is valid

        Raises:
            ValueError: If the workflow is invalid
        """
        self._validate_workflow_json()
        self._validate_input_image_path()
        self._validate_output_location()
        return True

    def _validate_workflow_json(self) -> None:
        """Validate workflow_json has valid ComfyUI structure.

        ComfyUI API workflows are flat dictionaries where root-level keys are
        node IDs (e.g., "136", "190") and values are node data dictionaries
        containing "class_type" and "inputs". The workflow may also contain
        standard fields like 'links', 'groups', 'config', 'extra', and 'version'.

        For testing purposes, the workflow may also use a simplified format where
        'nodes' is a list of node definitions.
        """
        if not isinstance(self.workflow_json, dict):
            raise ValueError("workflow_json must be a dictionary")

        if not self.workflow_json:
            raise ValueError("workflow_json must not be empty")

        # Standard ComfyUI workflow fields that are not node definitions
        standard_fields = {"links", "groups", "config", "extra", "version"}

        # Validate that all values are either dictionaries (node definitions),
        # one of the standard fields, or 'nodes' as a list (for mock workflows)
        for key, value in self.workflow_json.items():
            if key in standard_fields:
                # These fields have specific types we can optionally validate
                continue
            if key == "nodes" and isinstance(value, list):
                # Allow 'nodes' as a list for mock workflows in tests
                continue
            if not isinstance(value, dict):
                raise ValueError(
                    f"workflow_json values must be dictionaries (node definitions), "
                    f"but key '{key}' has value of type '{type(value).__name__}'"
                )

    def _validate_input_image_path(self) -> None:
        """Validate input_image_path points to an existing file."""
        path = Path(self.input_image_path)
        if not path.exists():
            raise ValueError(f"Input image does not exist: '{self.input_image_path}'")
        if not path.is_file():
            raise ValueError(
                f"Input image path is not a file: '{self.input_image_path}'"
            )

    def _validate_output_location(self) -> None:
        """Validate output_location is a valid directory path."""
        path = Path(self.output_location)
        if not path.exists():
            raise ValueError(
                f"Output location does not exist: '{self.output_location}'"
            )
        if not path.is_dir():
            raise ValueError(
                f"Output location is not a directory: '{self.output_location}'"
            )

    def to_dict(self) -> dict:
        """Convert the ComfyUIWorkflow to a dictionary.

        Returns:
            Dictionary representation of the ComfyUIWorkflow
        """
        return {
            "workflow_json": self.workflow_json,
            "input_image_path": self.input_image_path,
            "output_location": self.output_location,
            "prompt_id": self.prompt_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ComfyUIWorkflow":
        """Create a ComfyUIWorkflow from a dictionary.

        Args:
            data: Dictionary with ComfyUIWorkflow data

        Returns:
            New ComfyUIWorkflow instance
        """
        return cls(
            workflow_json=data["workflow_json"],
            input_image_path=data["input_image_path"],
            output_location=data["output_location"],
            prompt_id=data.get("prompt_id", ""),
        )

    def set_prompt_id(self, prompt_id: str) -> None:
        """Set the prompt ID after workflow trigger.

        Args:
            prompt_id: The prompt ID returned from ComfyUI API
        """
        self.prompt_id = prompt_id
