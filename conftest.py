"""Shared test fixtures for pytest."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_webcam():
    """Create a mock webcam capture object."""
    mock = MagicMock()
    mock.read.return_value = (True, MagicMock())
    return mock


@pytest.fixture
def mock_image():
    """Create a mock PIL Image object."""
    mock = MagicMock()
    mock.save = MagicMock()
    return mock


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    return tmp_path / "output"


@pytest.fixture
def temp_workflow_file(tmp_path):
    """Create a temporary workflow JSON file."""
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text('{"nodes": {}, "links": []}')
    return str(workflow_path)
