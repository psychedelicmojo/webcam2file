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
        """Validate workflow_json has valid ComfyUI structure."""
        if not isinstance(self.workflow_json, dict):
            raise ValueError("workflow_json must be a dictionary")

        # Basic validation: check for required ComfyUI workflow keys
        if "nodes" not in self.workflow_json:
            raise ValueError("workflow_json must contain 'nodes' key")

        if not isinstance(self.workflow_json["nodes"], (list, dict)):
            raise ValueError("workflow_json['nodes'] must be a list or dictionary")

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
