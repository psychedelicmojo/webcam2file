"""Comprehensive test for Tkinter/OpenCV/Pillow integration."""

import tkinter as tk

import cv2
import numpy as np
from PIL import Image, ImageTk


def test_basic_tkinter():
    """Test basic Tkinter functionality."""
    print("Test 1: Basic Tkinter")
    root = tk.Tk()
    root.title("Test 1: Basic Tkinter")

    label = tk.Label(root, text="If you see this, Tkinter works!")
    label.pack(padx=20, pady=20)

    root.after(1000, root.destroy)
    root.mainloop()
    print("  PASSED\n")


def test_opencv_capture():
    """Test OpenCV video capture."""
    print("Test 2: OpenCV Video Capture")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("  FAILED: Cannot open webcam")
        return False

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("  FAILED: Cannot read frame")
        return False

    print(f"  PASSED: Captured frame shape {frame.shape}")
    return True


def test_opencv_to_pil():
    """Test OpenCV to PIL conversion."""
    print("Test 3: OpenCV to PIL Conversion")

    # Create a test image
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    test_image[:, :] = [255, 0, 0]  # Red

    # Convert BGR to RGB
    rgb_image = cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB)

    # Convert to PIL
    pil_image = Image.fromarray(rgb_image)

    if pil_image is None:
        print("  FAILED: PIL conversion returned None")
        return False

    print(
        f"  PASSED: Converted to PIL Image mode={pil_image.mode}, size={pil_image.size}"
    )
    return True


def test_pil_to_photoimage():
    """Test PIL to PhotoImage conversion."""
    print("Test 4: PIL to PhotoImage Conversion")

    root = tk.Tk()
    root.withdraw()  # Hide window

    # Create a test image
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    test_image[:, :] = [0, 255, 0]  # Green
    rgb_image = cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)

    # Convert to PhotoImage
    try:
        ImageTk.PhotoImage(image=pil_image)
        print("  PASSED: Created PhotoImage")
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False
    finally:
        root.destroy()


def test_full_integration():
    """Test full integration: capture -> convert -> display."""
    print("Test 5: Full Integration (Capture -> Display)")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("  FAILED: Cannot open webcam")
        return False

    root = tk.Tk()
    root.title("Test 5: Full Integration")

    label = tk.Label(root)
    label.pack()

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("  FAILED: Cannot read frame")
        root.destroy()
        return False

    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert to PIL
    pil_image = Image.fromarray(rgb_frame)

    # Convert to PhotoImage
    try:
        photo = ImageTk.PhotoImage(image=pil_image)
        label.config(image=photo)
        label.image = photo  # Keep reference

        print("  PASSED: Displayed frame in Tkinter label")

        # Show window briefly
        root.after(500, root.destroy)
        root.mainloop()

        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        import traceback

        traceback.print_exc()
        root.destroy()
        return False


def test_webcam_with_opencv():
    """Test webcam capture with OpenCV directly."""
    print("Test 6: Webcam Capture with OpenCV")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("  FAILED: Cannot open webcam")
        return False

    # Read a few frames to ensure it's working
    for i in range(3):
        ret, frame = cap.read()
        if not ret:
            print(f"  FAILED: Cannot read frame {i + 1}")
            cap.release()
            return False

    print("  PASSED: Captured 3 frames successfully")
    cap.release()
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("Tkinter/OpenCV/Pillow Integration Tests")
    print("=" * 50)
    print()

    tests = [
        test_basic_tkinter,
        test_opencv_capture,
        test_opencv_to_pil,
        test_pil_to_photoimage,
        test_full_integration,
        test_webcam_with_opencv,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            if result is None:
                result = True  # Test passed if no exception
            results.append(result)
        except Exception as e:
            print(f"  EXCEPTION: {e}")
            import traceback

            traceback.print_exc()
            results.append(False)
        print()

    print("=" * 50)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 50)
