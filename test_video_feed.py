"""Debug script to test video feed display."""

import logging
import tkinter as tk

import cv2
from PIL import Image, ImageTk

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_video_feed():
    """Test video feed display with a simple Tkinter window."""
    root = tk.Tk()
    root.title("Webcam Test")

    # Create label for video
    video_label = tk.Label(root)
    video_label.pack()

    # Open webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("ERROR: Cannot open webcam")
        return

    print("Webcam opened successfully")

    def update_frame():
        """Update the video frame."""
        ret, frame = cap.read()

        if not ret:
            logger.error("Failed to read frame")
            root.after(100, update_frame)
            return

        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert to PhotoImage
        pil_image = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(image=pil_image)

        # Update label
        video_label.config(image=photo)
        video_label.image = photo  # Keep reference

        # Schedule next frame
        root.after(33, update_frame)

    # Start updating frames
    update_frame()

    # Run main loop
    root.mainloop()

    # Release webcam
    cap.release()


if __name__ == "__main__":
    test_video_feed()
