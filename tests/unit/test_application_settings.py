"""Unit tests for ApplicationSettings model."""

import json

import pytest

from src.models.application_settings import ApplicationSettings, WorkflowConfig, ArtStyleConfig


class TestApplicationSettingsUnit:
    """Unit tests for ApplicationSettings model."""

    def test_valid_settings(self, tmp_path):
        """Verify valid settings pass validation."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Create settings with valid values
        settings = ApplicationSettings(
            output_folder=str(output_folder),
            comfyui_endpoint="http://127.0.0.1:8188",
            workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
            art_styles=[
                ArtStyleConfig(name="", path=""),
                ArtStyleConfig(name="", path=""),
                ArtStyleConfig(name="", path=""),
                ArtStyleConfig(name="", path=""),
                ArtStyleConfig(name="", path=""),
            ],
            api_timeout=30,
        )

        # Verify all fields are set correctly
        assert settings.output_folder == str(output_folder)
        assert settings.comfyui_endpoint == "http://127.0.0.1:8188"
        assert len(settings.workflow_configs) == 4
        assert settings.workflow_configs[0].name == "Style 1"
        assert settings.workflow_configs[0].path == str(workflow_file)
        assert settings.api_timeout == 30

        # Verify validation passes
        assert settings.validate() is True

    def test_valid_settings_minimal(self, tmp_path):
        """Verify valid settings with minimal parameters pass validation."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Create settings with default api_timeout
        settings = ApplicationSettings(
            output_folder=str(output_folder),
            comfyui_endpoint="http://127.0.0.1:8188",
            workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
            art_styles=[
                ArtStyleConfig(name="", path=""),
                ArtStyleConfig(name="", path=""),
                ArtStyleConfig(name="", path=""),
                ArtStyleConfig(name="", path=""),
                ArtStyleConfig(name="", path=""),
            ],
        )

        # Verify default api_timeout is 30
        assert settings.api_timeout == 30

    def test_invalid_folder(self, tmp_path):
        """Verify ValueError for non-existent folder."""
        non_existent_folder = tmp_path / "non_existent_folder"

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Create settings with non-existent folder
        with pytest.raises(ValueError) as exc_info:
            ApplicationSettings(
                output_folder=str(non_existent_folder),
                comfyui_endpoint="http://127.0.0.1:8188",
                workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
            )

        # Verify error message
        assert "Output folder does not exist" in str(exc_info.value)

    def test_invalid_folder_not_a_directory(self, tmp_path):
        """Verify ValueError when output folder is not a directory."""
        # Create a file instead of a folder
        not_a_folder = tmp_path / "not_a_folder.txt"
        not_a_folder.write_text("test")

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Create settings with file instead of folder
        with pytest.raises(ValueError) as exc_info:
            ApplicationSettings(
                output_folder=str(not_a_folder),
                comfyui_endpoint="http://127.0.0.1:8188",
                workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
            )

        # Verify error message
        assert "Output folder is not a directory" in str(exc_info.value)

    def test_invalid_url(self, tmp_path):
        """Verify ValueError for invalid URL."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Test with invalid URL (no scheme)
        with pytest.raises(ValueError) as exc_info:
            ApplicationSettings(
                output_folder=str(output_folder),
                comfyui_endpoint="invalid-url",
                workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
            )

        # Verify error message
        assert "Invalid ComfyUI endpoint URL" in str(exc_info.value)

    def test_invalid_url_no_scheme(self, tmp_path):
        """Verify ValueError for URL without scheme."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Test with URL without scheme
        with pytest.raises(ValueError) as exc_info:
            ApplicationSettings(
                output_folder=str(output_folder),
                comfyui_endpoint="://127.0.0.1:8188",
                workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
            )

        # Verify error message
        assert "Invalid ComfyUI endpoint URL" in str(exc_info.value)

    def test_invalid_url_wrong_scheme(self, tmp_path):
        """Verify ValueError for URL with wrong scheme."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Test with FTP scheme (not allowed)
        with pytest.raises(ValueError) as exc_info:
            ApplicationSettings(
                output_folder=str(output_folder),
                comfyui_endpoint="ftp://127.0.0.1:8188",
                workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
            )

        # Verify error message
        assert "Invalid ComfyUI endpoint URL" in str(exc_info.value)

    def test_invalid_workflow_json_path(self, tmp_path):
        """Verify ValueError for non-existent workflow JSON file."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Test with non-existent workflow file
        with pytest.raises(ValueError) as exc_info:
            ApplicationSettings(
                output_folder=str(output_folder),
                comfyui_endpoint="http://127.0.0.1:8188",
                workflow_configs=[WorkflowConfig(name="Style 1", path=str(tmp_path / "non_existent_workflow.json"))],
            )

        # Verify error message
        assert "Workflow JSON file does not exist" in str(exc_info.value)

    def test_invalid_workflow_json_path_not_a_file(self, tmp_path):
        """Verify ValueError when workflow JSON path is not a file."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a directory instead of a file
        not_a_file = tmp_path / "not_a_file"
        not_a_file.mkdir()

        # Test with directory instead of file
        with pytest.raises(ValueError) as exc_info:
            ApplicationSettings(
                output_folder=str(output_folder),
                comfyui_endpoint="http://127.0.0.1:8188",
                workflow_configs=[WorkflowConfig(name="Style 1", path=str(not_a_file))],
            )

        # Verify error message
        assert "Workflow JSON path is not a file" in str(exc_info.value)

    def test_invalid_api_timeout(self, tmp_path):
        """Verify ValueError for invalid api_timeout."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Test with api_timeout = 0
        with pytest.raises(ValueError) as exc_info:
            ApplicationSettings(
                output_folder=str(output_folder),
                comfyui_endpoint="http://127.0.0.1:8188",
                workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
                api_timeout=0,
            )

        # Verify error message
        assert "Invalid api_timeout" in str(exc_info.value)

    def test_invalid_api_timeout_negative(self, tmp_path):
        """Verify ValueError for negative api_timeout."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Test with negative api_timeout
        with pytest.raises(ValueError) as exc_info:
            ApplicationSettings(
                output_folder=str(output_folder),
                comfyui_endpoint="http://127.0.0.1:8188",
                workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
                api_timeout=-5,
            )

        # Verify error message
        assert "Invalid api_timeout" in str(exc_info.value)

    def test_invalid_api_timeout_not_integer(self, tmp_path):
        """Verify ValueError for non-integer api_timeout."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Test with float api_timeout
        with pytest.raises(ValueError) as exc_info:
            ApplicationSettings(
                output_folder=str(output_folder),
                comfyui_endpoint="http://127.0.0.1:8188",
                workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
                api_timeout=30.5,
            )

        # Verify error message
        assert "Invalid api_timeout" in str(exc_info.value)

    def test_to_dict(self, tmp_path):
        """Verify to_dict() converts settings to dictionary correctly."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Create settings
        settings = ApplicationSettings(
            output_folder=str(output_folder),
            comfyui_endpoint="http://127.0.0.1:8188",
            workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
            api_timeout=60,
        )

        # Convert to dictionary
        result = settings.to_dict()

        # Verify dictionary contents
        assert result == {
            "output_folder": str(output_folder),
            "comfyui_endpoint": "http://127.0.0.1:8188",
            "workflow_configs": [
                {"name": "Style 1", "path": str(workflow_file)},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
            ],
            "api_timeout": 60,
            "art_styles": [
                {"name": "", "path": ""},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
            ],
            "email_address": "",
        }

    def test_from_dict(self, tmp_path):
        """Verify from_dict() creates settings from dictionary correctly."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Create dictionary
        data = {
            "output_folder": str(output_folder),
            "comfyui_endpoint": "http://127.0.0.1:8188",
            "workflow_configs": [
                {"name": "Style 1", "path": str(workflow_file)},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
            ],
            "api_timeout": 45,
        }

        # Create settings from dictionary
        settings = ApplicationSettings.from_dict(data)

        # Verify settings
        assert settings.output_folder == str(output_folder)
        assert settings.comfyui_endpoint == "http://127.0.0.1:8188"
        assert len(settings.workflow_configs) == 4
        assert settings.workflow_configs[0].name == "Style 1"
        assert settings.workflow_configs[0].path == str(workflow_file)
        assert settings.api_timeout == 45

    def test_from_dict_default_timeout(self, tmp_path):
        """Verify from_dict() uses default api_timeout when not provided."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Create dictionary without api_timeout
        data = {
            "output_folder": str(output_folder),
            "comfyui_endpoint": "http://127.0.0.1:8188",
            "workflow_configs": [
                {"name": "Style 1", "path": str(workflow_file)},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
            ],
        }

        # Create settings from dictionary
        settings = ApplicationSettings.from_dict(data)

        # Verify default api_timeout is 30
        assert settings.api_timeout == 30

    def test_save_to_file(self, tmp_path):
        """Verify save_to_file() saves settings to JSON file."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Create settings
        settings = ApplicationSettings(
            output_folder=str(output_folder),
            comfyui_endpoint="http://127.0.0.1:8188",
            workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
            api_timeout=30,
        )

        # Save to file
        settings_file = tmp_path / "settings.json"
        settings.save_to_file(str(settings_file))

        # Verify file exists
        assert settings_file.exists()

        # Verify file contents
        with open(settings_file, "r") as f:
            data = json.load(f)

        assert data == {
            "output_folder": str(output_folder),
            "comfyui_endpoint": "http://127.0.0.1:8188",
            "workflow_configs": [
                {"name": "Style 1", "path": str(workflow_file)},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
            ],
            "api_timeout": 30,
            "art_styles": [
                {"name": "", "path": ""},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
                {"name": "", "path": ""},
            ],
            "email_address": "",
        }

    def test_load_from_file(self, tmp_path):
        """Verify load_from_file() loads settings from JSON file."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Create settings
        settings = ApplicationSettings(
            output_folder=str(output_folder),
            comfyui_endpoint="http://127.0.0.1:8188",
            workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
            api_timeout=30,
        )

        # Save to file
        settings_file = tmp_path / "settings.json"
        settings.save_to_file(str(settings_file))

        # Load from file
        loaded_settings = ApplicationSettings.load_from_file(str(settings_file))

        # Verify loaded settings
        assert loaded_settings.output_folder == str(output_folder)
        assert loaded_settings.comfyui_endpoint == "http://127.0.0.1:8188"
        assert len(loaded_settings.workflow_configs) == 4
        assert loaded_settings.workflow_configs[0].name == "Style 1"
        assert loaded_settings.workflow_configs[0].path == str(workflow_file)
        assert loaded_settings.api_timeout == 30
        assert loaded_settings.art_styles == [
            ArtStyleConfig(name="", path=""),
            ArtStyleConfig(name="", path=""),
            ArtStyleConfig(name="", path=""),
            ArtStyleConfig(name="", path=""),
            ArtStyleConfig(name="", path=""),
        ]

    def test_persistence(self, tmp_path):
        """Verify settings save/load correctly."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Create original settings
        original_settings = ApplicationSettings(
            output_folder=str(output_folder),
            comfyui_endpoint="http://127.0.0.1:8188",
            workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
            api_timeout=45,
        )

        # Save to file
        settings_file = tmp_path / "settings.json"
        original_settings.save_to_file(str(settings_file))

        # Load from file
        loaded_settings = ApplicationSettings.load_from_file(str(settings_file))

        # Verify loaded settings match original
        assert loaded_settings.output_folder == original_settings.output_folder
        assert loaded_settings.comfyui_endpoint == original_settings.comfyui_endpoint
        assert len(loaded_settings.workflow_configs) == 4
        assert loaded_settings.workflow_configs[0].name == original_settings.workflow_configs[0].name
        assert loaded_settings.workflow_configs[0].path == original_settings.workflow_configs[0].path
        assert loaded_settings.api_timeout == original_settings.api_timeout
        assert loaded_settings.art_styles == original_settings.art_styles

        # Verify loaded settings are valid
        assert loaded_settings.validate() is True

    def test_https_endpoint(self, tmp_path):
        """Verify HTTPS endpoint is accepted."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Create settings with HTTPS endpoint
        settings = ApplicationSettings(
            output_folder=str(output_folder),
            comfyui_endpoint="https://127.0.0.1:8188",
            workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
        )

        # Verify validation passes
        assert settings.validate() is True

    def test_url_with_path(self, tmp_path):
        """Verify URL with path is accepted."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Create settings with URL containing path
        settings = ApplicationSettings(
            output_folder=str(output_folder),
            comfyui_endpoint="http://127.0.0.1:8188/api",
            workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
        )

        # Verify validation passes
        assert settings.validate() is True
