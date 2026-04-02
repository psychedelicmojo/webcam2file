"""Integration tests for User Story 3 - Settings and Configuration."""

import json
from pathlib import Path

import pytest

from src.models.application_settings import ApplicationSettings, WorkflowConfig
from src.models.comfyui_workflow import ComfyUIWorkflow


class TestUserStory3Integration:
    """Integration tests for User Story 3 - Settings and Configuration."""

    def test_settings_persistence(self, tmp_path):
        """Verify settings persist across restarts."""
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

        # Save to file (simulating application shutdown)
        settings_file = tmp_path / "settings.json"
        original_settings.save_to_file(str(settings_file))

        # Simulate application restart by loading from file
        loaded_settings = ApplicationSettings.load_from_file(str(settings_file))

        # Verify loaded settings match original
        assert loaded_settings.output_folder == original_settings.output_folder
        assert loaded_settings.comfyui_endpoint == original_settings.comfyui_endpoint
        assert len(loaded_settings.workflow_configs) == 4
        assert loaded_settings.workflow_configs[0].name == original_settings.workflow_configs[0].name
        assert loaded_settings.workflow_configs[0].path == original_settings.workflow_configs[0].path
        assert loaded_settings.api_timeout == original_settings.api_timeout

        # Verify loaded settings are valid (can be used immediately)
        assert loaded_settings.validate() is True

    def test_settings_persistence_multiple_fields(self, tmp_path):
        """Verify all settings fields persist correctly."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Create settings with various values
        original_settings = ApplicationSettings(
            output_folder=str(output_folder),
            comfyui_endpoint="http://localhost:8188",
            workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
            api_timeout=60,
        )

        # Save and load
        settings_file = tmp_path / "settings.json"
        original_settings.save_to_file(str(settings_file))
        loaded_settings = ApplicationSettings.load_from_file(str(settings_file))

        # Verify all fields match
        assert loaded_settings.output_folder == str(output_folder)
        assert loaded_settings.comfyui_endpoint == "http://localhost:8188"
        assert len(loaded_settings.workflow_configs) == 4
        assert loaded_settings.workflow_configs[0].path == str(workflow_file)
        assert loaded_settings.api_timeout == 60

    def test_connection_test_success(self, tmp_path):
        """Verify ComfyUI connection test works with valid endpoint."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Create settings with valid endpoint
        settings = ApplicationSettings(
            output_folder=str(output_folder),
            comfyui_endpoint="http://127.0.0.1:8188",
            workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
        )

        # Verify settings are valid
        assert settings.validate() is True

        # Note: This test verifies the settings structure is correct.
        # Actual API connection testing would require ComfyUI to be running.

    def test_connection_test_invalid_endpoint(self, tmp_path):
        """Verify connection test fails with invalid endpoint."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Test with invalid endpoint
        with pytest.raises(ValueError):
            ApplicationSettings(
                output_folder=str(output_folder),
                comfyui_endpoint="invalid-endpoint",
                workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
            )

    def test_workflow_validation_success(self, tmp_path):
        """Verify workflow JSON validation works with valid workflow."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a valid workflow file
        workflow_file = tmp_path / "workflow.json"
        valid_workflow = {
            "nodes": {
                "1": {
                    "class_type": "LoadImage",
                    "inputs": {"image": "example.jpg", "upload": "image"},
                },
                "2": {
                    "class_type": "KSampler",
                    "inputs": {
                        "model": ["1", 0],
                        "positive": ["1", 1],
                        "negative": ["1", 2],
                        "seed": 12345,
                    },
                },
            },
            "links": [[1, 0, 2, 0], [1, 1, 2, 1], [1, 2, 2, 2]],
            "groups": [],
            "config": {},
            "extra": {},
            "version": 0.4,
        }
        workflow_file.write_text(json.dumps(valid_workflow))

        # Create settings with valid workflow
        settings = ApplicationSettings(
            output_folder=str(output_folder),
            comfyui_endpoint="http://127.0.0.1:8188",
            workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
        )

        # Verify settings are valid
        assert settings.validate() is True

        # Verify workflow file exists and can be read
        assert Path(settings.workflow_configs[0].path).exists()

    def test_workflow_validation_missing_file(self, tmp_path):
        """Verify workflow validation fails with missing workflow file."""
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

    def test_workflow_validation_directory_not_file(self, tmp_path):
        """Verify workflow validation fails when path is directory."""
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

    def test_output_folder_validation(self, tmp_path):
        """Verify output folder validation works correctly."""
        # Test with non-existent folder
        non_existent = tmp_path / "non_existent"
        with pytest.raises(ValueError) as exc_info:
            ApplicationSettings(
                output_folder=str(non_existent),
                comfyui_endpoint="http://127.0.0.1:8188",
                workflow_configs=[WorkflowConfig(name="Style 1", path=str(tmp_path / "workflow.json"))],
            )
        assert "Output folder does not exist" in str(exc_info.value)

        # Create valid folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Test with valid folder
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        settings = ApplicationSettings(
            output_folder=str(output_folder),
            comfyui_endpoint="http://127.0.0.1:8188",
            workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
        )
        assert settings.validate() is True

    def test_api_timeout_validation(self, tmp_path):
        """Verify api_timeout validation works correctly."""
        # Create a temporary output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Create a temporary workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow_file.write_text('{"nodes": {}, "links": []}')

        # Test with valid timeout values
        for timeout in [1, 10, 30, 60, 120]:
            settings = ApplicationSettings(
                output_folder=str(output_folder),
                comfyui_endpoint="http://127.0.0.1:8188",
                workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
                api_timeout=timeout,
            )
            assert settings.validate() is True
            assert settings.api_timeout == timeout

        # Test with invalid timeout values
        for invalid_timeout in [0, -1, -10]:
            with pytest.raises(ValueError) as exc_info:
                ApplicationSettings(
                    output_folder=str(output_folder),
                    comfyui_endpoint="http://127.0.0.1:8188",
                    workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
                    api_timeout=invalid_timeout,
                )
            assert "Invalid api_timeout" in str(exc_info.value)

    def test_full_settings_workflow(self, tmp_path):
        """Verify complete settings workflow from creation to persistence."""
        # Step 1: Create output folder
        output_folder = tmp_path / "output"
        output_folder.mkdir()

        # Step 2: Create workflow file
        workflow_file = tmp_path / "workflow.json"
        workflow = {
            "nodes": {
                "1": {
                    "class_type": "LoadImage",
                    "inputs": {"image": "example.jpg", "upload": "image"},
                }
            },
            "links": [],
            "groups": [],
            "config": {},
            "extra": {},
            "version": 0.4,
        }
        workflow_file.write_text(json.dumps(workflow))

        # Step 3: Create settings
        settings = ApplicationSettings(
            output_folder=str(output_folder),
            comfyui_endpoint="http://127.0.0.1:8188",
            workflow_configs=[WorkflowConfig(name="Style 1", path=str(workflow_file))],
            api_timeout=30,
        )

        # Step 4: Validate settings
        assert settings.validate() is True

        # Step 5: Convert to dictionary
        settings_dict = settings.to_dict()
        assert "output_folder" in settings_dict
        assert "comfyui_endpoint" in settings_dict
        assert "workflow_configs" in settings_dict
        assert "api_timeout" in settings_dict

        # Step 6: Save to file
        settings_file = tmp_path / "settings.json"
        settings.save_to_file(str(settings_file))
        assert settings_file.exists()

        # Step 7: Load from file (simulating restart)
        loaded_settings = ApplicationSettings.load_from_file(str(settings_file))

        # Step 8: Verify loaded settings match original
        assert loaded_settings.output_folder == settings.output_folder
        assert loaded_settings.comfyui_endpoint == settings.comfyui_endpoint
        assert len(loaded_settings.workflow_configs) == 4
        assert loaded_settings.workflow_configs[0].name == settings.workflow_configs[0].name
        assert loaded_settings.workflow_configs[0].path == settings.workflow_configs[0].path
        assert loaded_settings.api_timeout == settings.api_timeout

        # Step 9: Verify loaded settings are valid
        assert loaded_settings.validate() is True

        # Step 10: Create a dummy image file for workflow validation
        test_image = output_folder / "test.jpg"
        test_image.write_bytes(b"fake_image_data")

        # Step 11: Verify loaded settings can create ComfyUIWorkflow
        workflow_obj = ComfyUIWorkflow(
            workflow_json=workflow,
            input_image_path=str(test_image),
            output_location=str(output_folder),
        )
        assert workflow_obj.validate() is True
