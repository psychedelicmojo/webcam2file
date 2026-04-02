"""Test script to verify webcam is working."""

import cv2


def test_webcam(index=0):
    """Test if a webcam at the given index is working."""
    print(f"Testing webcam at index {index}...")

    cap = cv2.VideoCapture(index)

    if not cap.isOpened():
        print(f"ERROR: Cannot open webcam at index {index}")
        return False

    # Try to read a frame
    ret, frame = cap.read()

    if not ret:
        print(f"ERROR: Cannot read frame from webcam at index {index}")
        cap.release()
        return False

    print(f"SUCCESS: Webcam at index {index} is working!")
    print(f"  Frame shape: {frame.shape}")
    print(f"  Frame size: {frame.nbytes} bytes")

    # Get actual resolution
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"  Resolution: {int(width)}x{int(height)}")

    cap.release()
    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        index = int(sys.argv[1])
        test_webcam(index)
    else:
        # Test first 10 webcams
        print("Testing first 10 webcam indices...")
        for i in range(10):
            test_webcam(i)
