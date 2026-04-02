"""ApplicationSettings model for user configuration."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse


@dataclass
class WorkflowConfig:
    """Configuration for a single workflow JSON file.

    Attributes:
        name: Display name for this workflow
        path: Path to the ComfyUI workflow JSON file
    """

    name: str
    path: str


@dataclass
class ArtStyleConfig:
    """Configuration for a single art style.

    Attributes:
        name: Display name for this art style
        path: Path to the art style file (image or JSON)
    """

    name: str
    path: str


@dataclass
class ApplicationSettings:
    """Represents user-configurable application preferences.

    Attributes:
        output_folder: Directory where captured images are saved
        comfyui_endpoint: ComfyUI API endpoint URL (optional, set to None to disable ComfyUI)
        workflow_configs: List of 10 workflow configurations (name + path pairs)
        art_styles: List of 5 art style configurations (name + path pairs)
        api_timeout: Timeout in seconds for API requests (default: 30)
        enable_comfyui: Whether ComfyUI integration is enabled (default: True)
        email_address: Email address for notifications (optional)
    """

    output_folder: str
    comfyui_endpoint: str
    workflow_configs: list[WorkflowConfig] = field(
        default_factory=lambda: [WorkflowConfig(name="", path="") for _ in range(10)]
    )
    art_styles: list[ArtStyleConfig] = field(
        default_factory=lambda: [
            ArtStyleConfig(name="", path=""),
            ArtStyleConfig(name="", path=""),
            ArtStyleConfig(name="", path=""),
            ArtStyleConfig(name="", path=""),
            ArtStyleConfig(name="", path=""),
        ]
    )
    api_timeout: int = 30
    enable_comfyui: bool = True
    email_address: str = ""
    apps_script_url: str = ""
    countdown_seconds: int = 3

    def __post_init__(self) -> None:
        """Validate the application settings after initialization."""
        # Ensure workflow_configs has exactly 10 entries
        if len(self.workflow_configs) < 10:
            while len(self.workflow_configs) < 10:
                self.workflow_configs.append(WorkflowConfig(name="", path=""))
        # Ensure art_styles has exactly 5 entries
        if len(self.art_styles) < 5:
            while len(self.art_styles) < 5:
                self.art_styles.append(ArtStyleConfig(name="", path=""))
        self.validate()

    def is_comfyui_enabled(self) -> bool:
        """Check if ComfyUI integration is enabled.

        Returns:
            True if ComfyUI is enabled and configured, False otherwise.
        """
        return self.enable_comfyui and any(
            config.path for config in self.workflow_configs
        )

    def get_workflow_config(self, index: int) -> WorkflowConfig | None:
        """Get workflow configuration by index.

        Args:
            index: Index of the workflow config (0-3)

        Returns:
            WorkflowConfig at the given index, or None if out of range
        """
        if 0 <= index < len(self.workflow_configs):
            return self.workflow_configs[index]
        return None

    def get_workflow_config_by_name(self, name: str) -> WorkflowConfig | None:
        """Get workflow configuration by name.

        Args:
            name: Display name of the workflow

        Returns:
            WorkflowConfig with matching name, or None if not found
        """
        for config in self.workflow_configs:
            if config.name == name:
                return config
        return None

    def validate(self) -> bool:
        """Validate all settings.

        Returns:
            True if all settings are valid

        Raises:
            ValueError: If any setting is invalid
        """
        self._validate_output_folder()
        # Only validate ComfyUI settings if ComfyUI is enabled
        if self.enable_comfyui:
            self._validate_comfyui_endpoint()
            # Validate all workflow configs that have paths
            for i, config in enumerate(self.workflow_configs):
                if config.path:
                    self._validate_workflow_config(i)
        self._validate_api_timeout()
        return True

    def _validate_output_folder(self) -> None:
        """Validate output_folder exists and is writable."""
        path = Path(self.output_folder)
        if not path.exists():
            raise ValueError(f"Output folder does not exist: '{self.output_folder}'")
        if not path.is_dir():
            raise ValueError(
                f"Output folder is not a directory: '{self.output_folder}'"
            )
        if not os.access(path, os.W_OK):
            raise ValueError(f"Output folder is not writable: '{self.output_folder}'")

    def _validate_comfyui_endpoint(self) -> None:
        """Validate comfyui_endpoint is a valid URL."""
        try:
            result = urlparse(self.comfyui_endpoint)
            if not all([result.scheme, result.netloc]):
                raise ValueError(
                    f"Invalid ComfyUI endpoint URL: '{self.comfyui_endpoint}'"
                )
            if result.scheme not in ("http", "https"):
                raise ValueError(
                    f"Invalid URL scheme: '{result.scheme}'. Must be http or https"
                )
        except Exception as e:
            raise ValueError(
                f"Invalid ComfyUI endpoint URL: '{self.comfyui_endpoint}'"
            ) from e

    def _validate_workflow_config(self, index: int) -> None:
        """Validate a specific workflow config path.

        Args:
            index: Index of the workflow config
        """
        config = self.workflow_configs[index]
        if config.path:
            path = Path(config.path)
            if not path.exists():
                raise ValueError(
                    f"Workflow JSON file does not exist for '{config.name}': '{config.path}'"
                )
            if not path.is_file():
                raise ValueError(
                    f"Workflow JSON path is not a file for '{config.name}': '{config.path}'"
                )

    def _validate_api_timeout(self) -> None:
        """Validate api_timeout is at least 1 second."""
        if not isinstance(self.api_timeout, int) or self.api_timeout < 1:
            raise ValueError(
                f"Invalid api_timeout: {self.api_timeout}. Must be an integer >= 1"
            )

    def to_dict(self) -> dict:
        """Convert the ApplicationSettings to a dictionary.

        Returns:
            Dictionary representation of the ApplicationSettings
        """
        return {
            "output_folder": self.output_folder,
            "comfyui_endpoint": self.comfyui_endpoint,
            "workflow_configs": [
                {"name": config.name, "path": config.path}
                for config in self.workflow_configs
            ],
            "api_timeout": self.api_timeout,
            "art_styles": [
                {"name": config.name, "path": config.path}
                for config in self.art_styles or []
            ],
            "email_address": self.email_address,
            "apps_script_url": self.apps_script_url,
            "countdown_seconds": self.countdown_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ApplicationSettings":
        """Create an ApplicationSettings from a dictionary.

        Args:
            data: Dictionary with ApplicationSettings data

        Returns:
            New ApplicationSettings instance
        """
        # Handle old format with workflow_json_path (single path string)
        if "workflow_json_path" in data:
            workflow_configs_data = [{"name": "Workflow 1", "path": data["workflow_json_path"]}]
        else:
            workflow_configs_data = data.get("workflow_configs", [])
        # Pad to exactly 10 slots (handles older settings files with fewer entries)
        while len(workflow_configs_data) < 10:
            workflow_configs_data.append({"name": "", "path": ""})
        workflow_configs = [
            WorkflowConfig(name=c["name"], path=c["path"])
            for c in workflow_configs_data
        ]
        art_styles_data = data.get(
            "art_styles",
            [
                {"name": "", "path": ""},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
            ],
        )
        # Ensure exactly 5 art styles
        while len(art_styles_data) < 5:
            art_styles_data.append({"name": "", "path": ""})
        art_styles = [
            ArtStyleConfig(name=c["name"], path=c["path"]) for c in art_styles_data
        ]
        return cls(
            output_folder=data["output_folder"],
            comfyui_endpoint=data["comfyui_endpoint"],
            workflow_configs=workflow_configs,
            api_timeout=data.get("api_timeout", 30),
            art_styles=art_styles,
            email_address=data.get("email_address", ""),
            apps_script_url=data.get("apps_script_url", ""),
            countdown_seconds=data.get("countdown_seconds", 3),
        )

    def save_to_file(self, filepath: str) -> None:
        """Save settings to a JSON file.

        Args:
            filepath: Path to the JSON file
        """
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "ApplicationSettings":
        """Load settings from a JSON file.

        Args:
            filepath: Path to the JSON file

        Returns:
            ApplicationSettings instance
        """
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)
