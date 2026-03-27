"""SettingsService for managing application configuration."""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from src.lib.error_manager import ErrorManager
from src.lib.logging_utils import LoggerManager
from src.models.application_settings import ApplicationSettings
from src.services.comfyui_service import APIConnectionError


class SettingsService:
    """Service for managing application settings.

    Provides methods to load, save, validate settings, and test connections
    to external services like ComfyUI.

    Attributes:
        settings_file: Path to the settings JSON file
        error_manager: Error manager for user-friendly error handling
    """

    DEFAULT_SETTINGS_FILE = "settings.json"
    DEFAULT_SETTINGS = {
        "output_folder": "captures",
        "comfyui_endpoint": "http://127.0.0.1:8188",
        "workflow_json_path": "workflow.json",
        "api_timeout": 30,
    }

    def __init__(
        self,
        settings_file: Optional[str] = None,
        error_manager: Optional[ErrorManager] = None,
    ):
        """Initialize the settings service.

        Args:
            settings_file: Path to the settings JSON file (default: settings.json)
            error_manager: Error manager for user-friendly error handling
        """
        self._settings_file = settings_file or self.DEFAULT_SETTINGS_FILE
        self._error_manager = error_manager or ErrorManager()
        self._current_settings: Optional[ApplicationSettings] = None

    def load_settings(self) -> ApplicationSettings:
        """Load settings from the settings file.

        Returns:
            ApplicationSettings: The loaded settings

        Raises:
            FileNotFoundError: If settings file doesn't exist
            ValueError: If settings are invalid
            json.JSONDecodeError: If settings file is not valid JSON
        """
        logger = LoggerManager.get_logger()
        logger.debug(f"Loading settings from '{self._settings_file}'")

        if not Path(self._settings_file).exists():
            logger.error(f"Settings file not found: '{self._settings_file}'")
            raise FileNotFoundError(
                f"Settings file not found: '{self._settings_file}'. "
                "Please configure settings first."
            )

        with open(self._settings_file, "r") as f:
            data = json.load(f)

        self._current_settings = ApplicationSettings.from_dict(data)
        logger.info(f"Settings loaded successfully from '{self._settings_file}'")
        return self._current_settings

    def save_settings(self, settings: ApplicationSettings) -> None:
        """Save settings to the settings file.

        Args:
            settings: ApplicationSettings to save
        """
        logger = LoggerManager.get_logger()
        logger.debug(f"Saving settings to '{self._settings_file}'")

        self._current_settings = settings
        settings.save_to_file(self._settings_file)
        logger.info(f"Settings saved successfully to '{self._settings_file}'")

    def validate_settings(self, settings: ApplicationSettings) -> bool:
        """Validate settings.

        Args:
            settings: ApplicationSettings to validate

        Returns:
            True if settings are valid

        Raises:
            ValueError: If settings are invalid
        """
        return settings.validate()

    def test_connection(self, settings: ApplicationSettings) -> Dict[str, str]:
        """Test connection to ComfyUI API.

        Args:
            settings: ApplicationSettings with ComfyUI endpoint

        Returns:
            Dictionary with connection test result information
        """
        logger = LoggerManager.get_logger()
        logger.debug(f"Testing connection to ComfyUI at {settings.comfyui_endpoint}")

        try:
            # Create a temporary ComfyUIService instance
            from src.services.comfyui_service_impl import ComfyUIService

            service = ComfyUIService(
                endpoint=settings.comfyui_endpoint,
                timeout=settings.api_timeout,
            )

            is_available = service.is_available()

            if is_available:
                logger.info(
                    f"Successfully connected to ComfyUI at {settings.comfyui_endpoint}"
                )
                return {
                    "success": "true",
                    "message": f"Connected to ComfyUI at {settings.comfyui_endpoint}",
                    "endpoint": settings.comfyui_endpoint,
                }
            else:
                logger.warning(
                    f"Failed to connect to ComfyUI at {settings.comfyui_endpoint}"
                )
                return {
                    "success": "false",
                    "message": f"Cannot connect to ComfyUI at {settings.comfyui_endpoint}",
                    "endpoint": settings.comfyui_endpoint,
                }

        except APIConnectionError as e:
            logger.error(
                f"API connection error when testing ComfyUI at {settings.comfyui_endpoint}: {str(e)}"
            )
            return {
                "success": "false",
                "message": str(e),
                "endpoint": settings.comfyui_endpoint,
            }
        except Exception as e:
            error_info = self._error_manager.handle_error(e)
            logger.error(
                f"Error testing ComfyUI connection at {settings.comfyui_endpoint}: {error_info['user_message']}"
            )
            return {
                "success": "false",
                "message": error_info["user_message"],
                "endpoint": settings.comfyui_endpoint,
            }

    def get_current_settings(self) -> Optional[ApplicationSettings]:
        """Get the currently loaded settings.

        Returns:
            ApplicationSettings if loaded, None otherwise
        """
        return self._current_settings

    def ensure_output_folder_exists(self, settings: ApplicationSettings) -> bool:
        """Ensure the output folder exists and is writable.

        Args:
            settings: ApplicationSettings with output_folder

        Returns:
            True if folder exists/was created, False otherwise
        """
        logger = LoggerManager.get_logger()
        path = Path(settings.output_folder)

        logger.debug(f"Checking output folder: '{settings.output_folder}'")

        try:
            if not path.exists():
                logger.info(f"Creating output folder: '{settings.output_folder}'")
                path.mkdir(parents=True, exist_ok=True)
            if not path.is_dir():
                logger.error(
                    f"Output folder is not a directory: '{settings.output_folder}'"
                )
                return False
            if not os.access(path, os.W_OK):
                logger.error(
                    f"Output folder is not writable: '{settings.output_folder}'"
                )
                return False
            logger.debug(f"Output folder is ready: '{settings.output_folder}'")
            return True
        except Exception as e:
            logger.error(
                f"Error ensuring output folder '{settings.output_folder}' exists: {str(e)}"
            )
            return False

    def get_default_settings(self) -> Dict[str, str]:
        """Get default settings values.

        Returns:
            Dictionary with default settings
        """
        return self.DEFAULT_SETTINGS.copy()
