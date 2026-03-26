"""ApplicationSettings model for user configuration."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass
class ApplicationSettings:
    """Represents user-configurable application preferences.
    
    Attributes:
        output_folder: Directory where captured images are saved
        comfyui_endpoint: ComfyUI API endpoint URL
        workflow_json_path: Path to the ComfyUI workflow JSON file
        api_timeout: Timeout in seconds for API requests (default: 30)
    """

    output_folder: str
    comfyui_endpoint: str
    workflow_json_path: str
    api_timeout: int = 30

    def __post_init__(self) -> None:
        """Validate the application settings after initialization."""
        self.validate()

    def validate(self) -> bool:
        """Validate all settings.
        
        Returns:
            True if all settings are valid
            
        Raises:
            ValueError: If any setting is invalid
        """
        self._validate_output_folder()
        self._validate_comfyui_endpoint()
        self._validate_workflow_json_path()
        self._validate_api_timeout()
        return True

    def _validate_output_folder(self) -> None:
        """Validate output_folder exists and is writable."""
        path = Path(self.output_folder)
        if not path.exists():
            raise ValueError(
                f"Output folder does not exist: '{self.output_folder}'"
            )
        if not path.is_dir():
            raise ValueError(
                f"Output folder is not a directory: '{self.output_folder}'"
            )
        if not os.access(path, os.W_OK):
            raise ValueError(
                f"Output folder is not writable: '{self.output_folder}'"
            )

    def _validate_comfyui_endpoint(self) -> None:
        """Validate comfyui_endpoint is a valid URL."""
        try:
            result = urlparse(self.comfyui_endpoint)
            if not all([result.scheme, result.netloc]):
                raise ValueError(
                    f"Invalid ComfyUI endpoint URL: '{self.comfyui_endpoint}'"
                )
            if result.scheme not in ('http', 'https'):
                raise ValueError(
                    f"Invalid URL scheme: '{result.scheme}'. "
                    f"Must be http or https"
                )
        except Exception as e:
            raise ValueError(
                f"Invalid ComfyUI endpoint URL: '{self.comfyui_endpoint}'"
            ) from e

    def _validate_workflow_json_path(self) -> None:
        """Validate workflow_json_path points to an existing file."""
        path = Path(self.workflow_json_path)
        if not path.exists():
            raise ValueError(
                f"Workflow JSON file does not exist: '{self.workflow_json_path}'"
            )
        if not path.is_file():
            raise ValueError(
                f"Workflow JSON path is not a file: '{self.workflow_json_path}'"
            )

    def _validate_api_timeout(self) -> None:
        """Validate api_timeout is at least 1 second."""
        if not isinstance(self.api_timeout, int) or self.api_timeout < 1:
            raise ValueError(
                f"Invalid api_timeout: {self.api_timeout}. "
                f"Must be an integer >= 1"
            )

    def to_dict(self) -> dict:
        """Convert the ApplicationSettings to a dictionary.
        
        Returns:
            Dictionary representation of the ApplicationSettings
        """
        return {
            'output_folder': self.output_folder,
            'comfyui_endpoint': self.comfyui_endpoint,
            'workflow_json_path': self.workflow_json_path,
            'api_timeout': self.api_timeout,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ApplicationSettings':
        """Create an ApplicationSettings from a dictionary.
        
        Args:
            data: Dictionary with ApplicationSettings data
            
        Returns:
            New ApplicationSettings instance
        """
        return cls(
            output_folder=data['output_folder'],
            comfyui_endpoint=data['comfyui_endpoint'],
            workflow_json_path=data['workflow_json_path'],
            api_timeout=data.get('api_timeout', 30),
        )

    def save_to_file(self, filepath: str) -> None:
        """Save settings to a JSON file.
        
        Args:
            filepath: Path to the JSON file
        """
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'ApplicationSettings':
        """Load settings from a JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            ApplicationSettings instance
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
