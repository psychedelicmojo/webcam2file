"""ImageCapture model for tracking captured frames."""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImageCapture:
    """Represents a single frame captured from the webcam.
    
    Attributes:
        timestamp: Timestamp of capture in YYYYMMDD_HHmmss format
        filepath: Full path to the saved JPEG file
        filesize: Size of the file in bytes
        output_folder: Directory where the image was saved
        status: Current processing status (pending, processing, completed, error)
    """

    timestamp: str
    filepath: str
    filesize: int
    output_folder: str
    status: str = "pending"

    # Validation patterns
    TIMESTAMP_PATTERN = re.compile(r'^\d{8}_\d{6}$')
    JPEG_EXTENSION = '.jpg'

    def __post_init__(self) -> None:
        """Validate the image capture data after initialization."""
        self._validate_timestamp()
        self._validate_filepath()
        self._validate_filesize()
        self._validate_output_folder()
        self._validate_status()

    def _validate_timestamp(self) -> None:
        """Validate timestamp format."""
        if not self.TIMESTAMP_PATTERN.match(self.timestamp):
            raise ValueError(
                f"Invalid timestamp format: '{self.timestamp}'. "
                f"Expected format: YYYYMMDD_HHmmss"
            )

    def _validate_filepath(self) -> None:
        """Validate filepath ends with .jpg extension."""
        if not self.filepath.endswith(self.JPEG_EXTENSION):
            raise ValueError(
                f"Invalid filepath: '{self.filepath}'. "
                f"File must have .jpg extension"
            )

    def _validate_filesize(self) -> None:
        """Validate filesize is greater than 0."""
        if self.filesize <= 0:
            raise ValueError(
                f"Invalid filesize: {self.filesize}. "
                f"Filesize must be greater than 0"
            )

    def _validate_output_folder(self) -> None:
        """Validate output_folder is a valid directory path."""
        path = Path(self.output_folder)
        if not path.is_absolute():
            raise ValueError(
                f"Invalid output_folder: '{self.output_folder}'. "
                f"Must be an absolute path"
            )

    def _validate_status(self) -> None:
        """Validate status is one of the allowed values."""
        valid_statuses = {'pending', 'processing', 'completed', 'error'}
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid status: '{self.status}'. "
                f"Must be one of: {', '.join(valid_statuses)}"
            )

    def update_status(self, new_status: str) -> None:
        """Update the processing status with validation.
        
        Args:
            new_status: The new status value
            
        Raises:
            ValueError: If the new status is invalid
        """
        valid_statuses = {'pending', 'processing', 'completed', 'error'}
        if new_status not in valid_statuses:
            raise ValueError(
                f"Invalid status: '{new_status}'. "
                f"Must be one of: {', '.join(valid_statuses)}"
            )
        self.status = new_status

    def to_dict(self) -> dict:
        """Convert the ImageCapture to a dictionary.
        
        Returns:
            Dictionary representation of the ImageCapture
        """
        return {
            'timestamp': self.timestamp,
            'filepath': self.filepath,
            'filesize': self.filesize,
            'output_folder': self.output_folder,
            'status': self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ImageCapture':
        """Create an ImageCapture from a dictionary.
        
        Args:
            data: Dictionary with ImageCapture data
            
        Returns:
            New ImageCapture instance
        """
        return cls(
            timestamp=data['timestamp'],
            filepath=data['filepath'],
            filesize=data['filesize'],
            output_folder=data['output_folder'],
            status=data.get('status', 'pending'),
        )
