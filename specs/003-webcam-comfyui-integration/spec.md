# Feature Specification: Webcam-to-ComfyUI Desktop Application

**Feature Branch**: `003-webcam-comfyui-integration`
**Created**: 2026-03-25
**Status**: Draft
**Input**: User description: "Build a desktop application that displays a live video feed from a connected high-definition webcam. The primary user interaction is pressing the space bar, which captures the current frame and saves it as a JPEG image to a monitored local folder. The application must actively watch this folder and, upon detecting a new image file, automatically trigger a local ComfyUI workflow via its API. This workflow will take the captured image and process it using a specific ComfyUI JSON file to apply an art style. The application should provide basic on-screen visual feedback when a picture is successfully captured and when the ComfyUI processing is initiated."

## Clarifications

### Session 2026-03-25

- Q: For captured image filenames to ensure uniqueness, what naming convention should be used? → A: Timestamp-based naming (e.g., capture_20260325_214530.jpg)
- Q: Where should captured images be saved by default? → A: User-selectable folder via settings UI
- Q: What form should visual feedback take when an image is captured or processing starts? → A: Visual flash/border highlight (subtle screen effect)
- Q: How should the ComfyUI workflow configuration be specified? → A: File path to a pre-saved JSON file (user selects via file picker)
- Q: What should happen when the user presses the space bar while a ComfyUI workflow is already processing another image? → A: Queue the capture (process after current workflow completes)

## User Scenarios & Testing

### User Story 1 - Capture and Save Image (Priority: P1)

A user opens the application, sees a live video feed from their webcam, and presses the space bar to capture the current frame. The application saves the captured image as a JPEG file to a designated local folder and provides visual feedback that the capture was successful.

**Why this priority**: This is the core value proposition of the application - capturing images from a webcam. Without this functionality, there is no application. This represents the minimum viable product that delivers immediate value.

**Independent Test**: Can be fully tested by opening the application, verifying the video feed displays, pressing space bar, and confirming a JPEG file is created in the output folder with visual feedback shown on screen.

**Acceptance Scenarios**:

1. **Given** the application is running with a connected high-definition webcam, **When** the user presses the space bar, **Then** the current video frame is captured and saved as a JPEG file to the designated output folder, and visual feedback is displayed on screen.

2. **Given** the application is running, **When** the user presses the space bar multiple times in quick succession, **Then** each capture is saved as a separate file with unique naming to prevent overwrites.

3. **Given** no webcam is connected, **When** the user attempts to open the application, **Then** an appropriate error message is displayed indicating no webcam is available.

---

### User Story 2 - Monitor Folder and Trigger ComfyUI Workflow (Priority: P1)

The application continuously monitors the output folder for new image files. When a new image is detected, the application automatically sends a request to the local ComfyUI API to process the image using a pre-configured workflow JSON file, and provides visual feedback that processing has begun.

**Why this priority**: This is the second critical component that completes the user's primary workflow. Without automatic folder monitoring and ComfyUI integration, the user would need to manually trigger the art style processing, defeating the purpose of automation.

**Independent Test**: Can be fully tested by capturing an image (from User Story 1), verifying the application detects the new file, confirms ComfyUI API connection, and shows visual feedback that processing has started.

**Acceptance Scenarios**:

1. **Given** a new JPEG image has been saved to the monitored output folder, **When** the application detects the file, **Then** it automatically sends a request to the local ComfyUI API with the image path and workflow configuration, and visual feedback indicates processing has begun.

2. **Given** the ComfyUI API is not accessible, **When** the application attempts to trigger a workflow, **Then** an appropriate error message is displayed with options to retry or cancel.

3. **Given** multiple images are saved to the folder in quick succession, **When** the application detects each file, **Then** each image is processed in sequence without conflicts or data corruption.

---

### User Story 3 - Apply Art Style and Display Result (Priority: P2)

The ComfyUI workflow processes the captured image using the specified art style configuration and saves the result to a designated output location. The application provides visual feedback when processing is complete and displays the processed image to the user.

**Why this priority**: This represents the final step in the user's desired workflow - receiving the art-styled result. While important for complete user satisfaction, the core value (capture + trigger) can be demonstrated without the final display of results.

**Independent Test**: Can be fully tested by verifying the processed image appears in the expected output location and is displayed to the user after ComfyUI processing completes.

**Acceptance Scenarios**:

1. **Given** the ComfyUI workflow has completed processing, **When** the processed image is available, **Then** it is saved to the designated output location and visual feedback indicates processing completion.

2. **Given** the ComfyUI workflow fails or produces an error, **When** the error is detected, **Then** an appropriate error message is displayed with details about what went wrong.

3. **Given** the user wants to review the processed result, **When** processing completes, **Then** the processed image can be viewed in the application or opened in the default image viewer.

---

### Edge Cases

- **Queue Behavior**: When the user presses the space bar while a ComfyUI workflow is already processing another image, the new capture is queued and processed in sequence after the current workflow completes.

- **Output Folder Inaccessible**: If the output folder becomes inaccessible (permissions changed, drive disconnected), the application displays an error message with options to select a new folder or retry.

- **ComfyUI Service Unavailable**: If the ComfyUI service is temporarily unavailable during workflow trigger, the application displays an error message with retry/cancel options and queues the capture for later processing when the service becomes available.

- **Very Large Image Files**: If an image file exceeds memory limits or API payload sizes, the application displays an error message indicating the file is too large and suggests resizing or using a different workflow.

- **Multiple Application Instances**: If multiple instances of the application are running simultaneously and monitoring the same folder, the application displays a warning that this configuration is not recommended and may cause conflicts.

## Requirements

### Functional Requirements

- **FR-001**: System MUST display a live video feed from a connected high-definition webcam when the application is launched.

- **FR-002**: System MUST capture the current video frame when the user presses the space bar and save it as a JPEG image file to a user-configurable output folder specified via the application settings UI.

- **FR-003**: System MUST provide visual feedback on screen when an image is successfully captured using a subtle flash or border highlight effect around the video feed area.

- **FR-004**: System MUST continuously monitor the designated output folder for new image files.

- **FR-005**: System MUST automatically detect when a new JPEG image file is added to the monitored folder.

- **FR-006**: System MUST send a request to the local ComfyUI API to trigger the art style processing workflow when a new image is detected.

- **FR-007**: System MUST include the path to the captured image and the workflow configuration (from a user-selected JSON file via file picker in settings) in the ComfyUI API request.

- **FR-008**: System MUST provide visual feedback on screen when ComfyUI processing has been initiated using a subtle flash or border highlight effect around the video feed area.

- **FR-009**: System MUST provide visual feedback on screen when ComfyUI processing has completed successfully using a subtle flash or border highlight effect around the video feed area.

- **FR-010**: System MUST handle cases where no webcam is connected by displaying an appropriate error message.

- **FR-011**: System MUST handle cases where the ComfyUI API is not accessible by displaying an appropriate error message with retry options.

- **FR-012**: System MUST handle cases where the output folder becomes inaccessible by displaying an appropriate error message.

- **FR-013**: System MUST assign unique filenames to each captured image using timestamp-based naming (format: `capture_YYYYMMDD_HHmmss.jpg`) to prevent overwrites when multiple captures occur.

- **FR-014**: System MUST process multiple images sequentially when they are saved to the folder in quick succession.

- **FR-015**: System MUST handle ComfyUI workflow errors gracefully by displaying appropriate error messages with details.

- **FR-016**: System MUST queue captures when the user presses the space bar while another workflow is in progress, ensuring each captured image is processed in sequence after the current workflow completes.

### Key Entities

- **Image Capture**: Represents a single frame captured from the webcam. Key attributes include timestamp (in `YYYYMMDD_HHmmss` format), file path (using timestamp-based naming convention `capture_YYYYMMDD_HHmmss.jpg`), file size, and output folder path. Each capture is saved as a separate JPEG file in the user-configured output folder.

- **Application Settings**: Represents user-configurable application preferences. Key attributes include output folder path (user-selectable via settings UI), ComfyUI API endpoint URL, and workflow JSON file path (user-selected via file picker dialog).

- **ComfyUI Workflow**: Represents the art style processing configuration. Key attributes include the workflow JSON configuration, input image path, and output location. Each workflow processes one image at a time.

- **Processing Status**: Represents the current state of image processing (idle, processing, completed, error). Tracks which image is being processed and any associated error messages.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can capture and save an image within 2 seconds of pressing the space bar.

- **SC-002**: The application detects new images and triggers ComfyUI processing within 5 seconds of the file being saved.

- **SC-003**: Visual feedback appears on screen within 1 second of each significant event (capture, processing start, processing completion).

- **SC-004**: The application successfully handles 95% of common error scenarios (no webcam, API unavailable, folder inaccessible) without crashing.

- **SC-005**: Users can complete the full workflow (capture → process → receive result) in under 3 minutes for typical image sizes.

- **SC-006**: 90% of users successfully complete their first capture on the first attempt without external assistance.

## Assumptions

- Users have a compatible high-definition webcam connected to their desktop computer.

- The ComfyUI service is running locally on the same machine and is accessible via standard API endpoints.

- The output folder for captured images has sufficient storage space and appropriate write permissions.

- The ComfyUI workflow JSON file is pre-configured and accessible to the application.

- The application runs on a desktop operating system (Windows, macOS, or Linux) with sufficient processing power for real-time video display and image processing.

- Network connectivity to the local ComfyUI service is stable and has low latency.

- Image files will be of reasonable size (typical webcam capture dimensions) that don't exceed API payload limits.
