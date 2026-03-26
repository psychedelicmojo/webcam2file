# Research: Webcam-to-ComfyUI Desktop Application

**Feature Branch**: `003-webcam-comfyui-integration`  
**Date**: 2026-03-25

## Overview

This document consolidates research findings for implementing a desktop application that captures webcam images and processes them through a local ComfyUI workflow.

---

## Research Topics

### 1. Webcam Video Capture on Windows

**Question**: What is the best approach for capturing live video from a high-definition webcam on Windows 11?

**Research Findings**:

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| OpenCV (cv2) | Mature, cross-platform, good performance, Python bindings | Additional dependency, requires OpenCV DLLs | ✅ **Primary choice** |
| DirectShow | Native Windows, fine-grained control | Windows-only, complex API | Not recommended |
| Media Foundation | Modern Windows API, hardware acceleration | Windows-only, complex setup | Not recommended |
| PyGame | Simple, cross-platform | Limited camera support, not ideal for video | Not recommended |

**Decision**: Use **OpenCV (cv2)** for video capture. It provides reliable HD video capture with good performance and is well-documented for desktop applications.

**Rationale**: OpenCV is the industry standard for computer vision tasks including video capture. It works consistently across Windows, macOS, and Linux, making future platform expansion possible. The Python bindings are mature and well-supported.

**Alternatives considered**: DirectShow and Media Foundation were rejected due to Windows-only limitation and complexity. PyGame was rejected due to limited camera support.

**Implementation Notes**:
- Use `cv2.VideoCapture(0)` for default webcam
- Set resolution: `cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)` and `cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)`
- Use `cap.read()` for frame capture
- Release with `cap.release()` on application close

---

### 2. File System Monitoring

**Question**: What is the best approach for monitoring a folder for new image files?

**Research Findings**:

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| watchdog | Cross-platform, event-driven, Pythonic | Additional dependency | ✅ **Primary choice** |
| pyinotify | Linux-only, event-driven | Linux-only | Not recommended |
| winotify | Windows-only, event-driven | Windows-only | Not recommended |
| Polling (time.sleep) | Simple, no dependencies | CPU-intensive, delayed detection | Not recommended |

**Decision**: Use **watchdog** for file system monitoring. It provides event-driven monitoring with minimal CPU overhead and works across platforms.

**Rationale**: Event-driven monitoring is more efficient than polling and provides immediate notification of file changes. watchdog is the most mature Python library for this purpose.

**Alternatives considered**: Platform-specific solutions (pyinotify, winotify) were rejected due to platform limitations. Polling was rejected due to CPU inefficiency.

**Implementation Notes**:
- Use `watchdog.observers.Observer` with `watchdog.events.FileSystemEventHandler`
- Filter for JPEG files only
- Handle file system race conditions (file may still be writing)

---

### 3. ComfyUI API Integration

**Question**: How should the application communicate with the local ComfyUI API?

**Research Findings**:

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| requests library | Simple, mature, Python standard | Synchronous, blocking | ✅ **Primary choice** |
| aiohttp | Async, modern | Async complexity for simple use case | Not recommended |
| urllib3 | Low-level, flexible | More complex than needed | Not recommended |

**Decision**: Use **requests** library for ComfyUI API communication.

**Rationale**: The ComfyUI workflow triggering is a simple POST request followed by periodic status checks. The synchronous nature of requests is acceptable for this use case. Async would add unnecessary complexity.

**ComfyUI API Endpoints**:
- `POST /prompt` - Submit workflow with inputs
- `GET /history/{prompt_id}` - Check workflow status
- `GET /view/{filename}` - Retrieve output images

**Implementation Notes**:
- ComfyUI typically runs on `http://127.0.0.1:8188`
- Workflow JSON must include input image path
- Handle API timeouts (configurable, default 30s)
- Implement retry logic for transient failures

---

### 4. Image Processing and JPEG Saving

**Question**: What library should be used for image capture and JPEG saving?

**Research Findings**:

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| Pillow (PIL) | Python standard, easy JPEG saving, image manipulation | Additional dependency | ✅ **Primary choice** |
| OpenCV | Can save JPEGs, image processing capabilities | Overkill for simple save | Not recommended |
| imageio | Simple, supports many formats | Additional dependency | Not recommended |

**Decision**: Use **Pillow (PIL)** for JPEG saving and basic image operations.

**Rationale**: Pillow is the Python standard for image processing and provides simple, reliable JPEG saving. OpenCV can save JPEGs but would be overkill for this simple use case.

**Implementation Notes**:
- Convert OpenCV BGR to RGB before saving with Pillow
- Use `Image.fromarray()` to convert numpy array to PIL Image
- Save with `image.save(path, 'JPEG', quality=95)`

---

### 5. Cross-Platform Considerations

**Question**: Should the application support macOS and Linux?

**Research Findings**:

| Platform | Webcam Support | File Monitoring | ComfyUI |
|----------|---------------|-----------------|---------|
| Windows 11 | ✅ OpenCV | ✅ watchdog | ✅ Local |
| macOS | ✅ OpenCV | ✅ watchdog | ✅ Local |
| Linux | ✅ OpenCV | ✅ watchdog | ✅ Local |

**Decision**: Build for Windows 11 primarily, but design for cross-platform compatibility.

**Rationale**: The specification mentions Windows, macOS, and Linux as target platforms. Using cross-platform libraries (OpenCV, watchdog, requests, Pillow) enables future expansion without code changes.

**Implementation Notes**:
- Use `platform.system()` for platform-specific code paths if needed
- Test on all target platforms before release
- Document platform-specific requirements

---

## Dependencies Summary

| Library | Purpose | Version | Notes |
|---------|---------|---------|-------|
| opencv-python | Video capture | ^4.8.0 | Primary video capture |
| watchdog | File monitoring | ^2.1.0 | Event-driven folder monitoring |
| requests | ComfyUI API | ^2.31.0 | HTTP client |
| Pillow | Image processing | ^10.0.0 | JPEG saving, image ops |
| pytest | Testing | ^7.4.0 | Unit and integration tests |

---

## Technical Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Webcam not accessible | High | Graceful error handling, user notification |
| ComfyUI API unavailable | High | Retry logic, queue for later processing |
| File system race conditions | Medium | Wait for file to be fully written before processing |
| Large image files | Medium | Check file size before processing, warn user |
| Multiple instances | Low | Check for existing instance, warn user |

---

## Next Steps

1. **Phase 1 Design**: Define data models, service interfaces, and UI contracts
2. **Test Strategy**: Write contract tests for services before implementation
3. **Architecture Review**: Ensure modular architecture meets constitution requirements
