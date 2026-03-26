# Tasks: Webcam-to-ComfyUI Desktop Application

**Input**: Design documents from `/specs/003-webcam-comfyui-integration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Contract tests and integration tests are included for each user story. Tests are written FIRST per TDD requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
  - Create `src/models/`, `src/services/`, `src/ui/`, `src/cli/`, `src/lib/` directories
  - Create `tests/contract/`, `tests/integration/`, `tests/unit/` directories
  - Create `requirements.txt` with dependencies: opencv-python, pillow, requests, watchdog, pytest

- [ ] T002 [P] Configure linting and formatting tools
  - Create `.ruff.toml` with Python 3.11 configuration
  - Create `.editorconfig` for consistent code style
  - Add pre-commit hook for ruff check before commits

- [ ] T003 [P] Setup pytest configuration
  - Create `pytest.ini` with test discovery paths
  - Create `conftest.py` for shared test fixtures

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Foundational Models

- [ ] T004 [P] Create `ImageCapture` model in `src/models/image_capture.py`
  - Fields: timestamp (str), filepath (str), filesize (int), output_folder (str), status (str)
  - Validation: timestamp format `YYYYMMDD_HHmmss`, filepath ends with `.jpg`, filesize > 0
  - State transitions: `pending → processing → completed/error`

- [ ] T005 [P] Create `ApplicationSettings` model in `src/models/application_settings.py`
  - Fields: output_folder (str), comfyui_endpoint (str), workflow_json_path (str), api_timeout (int, default 30)
  - Validation: output_folder exists and writable, comfyui_endpoint valid URL, workflow_json_path exists
  - Methods: `validate()`, `to_dict()`, `from_dict()`

- [ ] T006 [P] Create `ComfyUIWorkflow` model in `src/models/comfyui_workflow.py`
  - Fields: workflow_json (dict), input_image_path (str), output_location (str), prompt_id (str, optional)
  - Validation: workflow_json valid ComfyUI structure, input_image_path exists
  - Methods: `validate()`, `to_dict()`

- [ ] T007 [P] Create `ProcessingStatus` model in `src/models/processing_status.py`
  - Fields: state (str), current_image (str, optional), error_message (str, optional), queue_size (int)
  - State values: `idle`, `processing`, `completed`, `error`
  - State transitions: `idle → processing → completed/error → idle`

### Foundational Services (Interfaces)

- [ ] T008 [P] Create `IWebcamService` interface in `src/services/webcam_service.py`
  - Methods: `start()`, `stop()`, `capture_frame()`, `is_running()`
  - Exceptions: `WebcamNotFoundError`, `WebcamAccessError`, `WebcamNotStartedError`, `CaptureError`

- [ ] T009 [P] Create `IFileMonitorService` interface in `src/services/file_monitor_service.py`
  - Methods: `start_monitoring()`, `stop_monitoring()`, `is_monitoring()`
  - Callback: `on_file_created(filepath: str)`
  - Exceptions: `FolderNotFoundError`, `FolderAccessError`

- [ ] T010 [P] Create `IComfyUIService` interface in `src/services/comfyui_service.py`
  - Methods: `trigger_workflow()`, `check_status()`, `is_available()`
  - Exceptions: `APIConnectionError`, `APIError`, `TimeoutError`

- [ ] T011 [P] Create `ICaptureQueue` interface in `src/services/capture_queue.py`
  - Methods: `enqueue()`, `dequeue()`, `get_queue_size()`, `get_processing_state()`, `set_processing_state()`, `is_processing()`
  - Enum: `ProcessingState` (IDLE, PROCESSING, COMPLETED, ERROR)

### Foundational Utilities

- [ ] T012 [P] Create `VisualFeedback` service in `src/services/visual_feedback.py`
  - Methods: `show_capture_feedback()`, `show_processing_feedback()`, `show_completion_feedback()`, `show_error_feedback(message)`, `hide_feedback()`
  - Visual effects: subtle flash/border highlight around video feed area

- [ ] T013 [P] Create `ErrorManager` utility in `src/lib/error_manager.py`
  - Methods: `handle_error(error, user_message)`, `get_recovery_action(error_type)`
  - Error types: `WebcamNotFoundError`, `WebcamAccessError`, `FolderNotFoundError`, `FolderAccessError`, `APIConnectionError`, `APIError`, `TimeoutError`

- [ ] T014 [P] Create `FileUtils` utility in `src/lib/file_utils.py`
  - Methods: `generate_unique_filename(prefix='capture', suffix='.jpg')`, `wait_for_file_ready(filepath, timeout=5)`
  - Handles file system race conditions

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Capture and Save Image (Priority: P1) 🎯 MVP

**Goal**: Display live video feed and capture frames via space bar

**Independent Test**: Open application, verify video feed displays, press space bar, confirm JPEG file created in output folder with visual feedback

### Tests for User Story 1 (TDD - Write FIRST) ⚠️

- [ ] T015 [P] [US1] Contract test for `IWebcamService` in `tests/contract/test_webcam_service.py`
  - `test_start_success`: Verify start() initializes webcam without errors
  - `test_start_no_webcam`: Verify WebcamNotFoundError when no webcam available
  - `test_capture_frame`: Verify capture_frame() returns valid JPEG data
  - `test_stop`: Verify stop() releases webcam resources

- [ ] T016 [P] [US1] Contract test for `CaptureService` in `tests/contract/test_capture_service.py`
  - `test_capture_and_save`: Verify frame capture and JPEG save to output folder
  - `test_unique_filename`: Verify timestamp-based unique filenames
  - `test_visual_feedback`: Verify visual feedback is triggered on capture

- [ ] T017 [P] [US1] Integration test for full capture workflow in `tests/integration/test_user_story_1.py`
  - `test_full_capture_workflow`: Verify complete capture → save → feedback workflow
  - `test_multiple_captures`: Verify multiple captures create separate files
  - `test_no_webcam_error`: Verify error handling when no webcam available
  - `test_concurrent_captures`: Verify queue handles multiple captures in sequence

---

## Phase 3.5: TDD Enforcement Checkpoint

**Purpose**: Verify all contract and integration tests for User Story 1 pass before implementation begins

**⚠️ CRITICAL**: No implementation tasks can begin until all tests in this checkpoint pass

- [ ] T017A [P] [US1] Verify all contract tests for `IWebcamService` pass
- [ ] T017B [P] [US1] Verify all contract tests for `CaptureService` pass
- [ ] T017C [P] [US1] Verify all integration tests for User Story 1 pass

---

## Phase 4: User Story 2 - Monitor Folder and Trigger ComfyUI Workflow (Priority: P1)

### Implementation for User Story 1

- [ ] T018 [P] [US1] Create `CaptureService` in `src/services/capture_service.py`
  - Dependencies: `IWebcamService`, `ApplicationSettings`, `VisualFeedback`
  - Methods: `capture_and_save()`, `get_current_frame()`
  - Uses `FileUtils.generate_unique_filename()` for unique filenames

- [ ] T019 [P] [US1] Create `WebcamServiceImpl` in `src/services/webcam_impl.py`
  - Implements `IWebcamService` using OpenCV
  - Methods: `start()`, `stop()`, `capture_frame()`, `is_running()`
  - Resolution: 1920x1080 HD

- [ ] T020 [US1] Implement main window UI in `src/ui/main_window.py`
  - Video feed display using OpenCV
  - Space bar key handler for capture
  - Visual feedback integration
  - Error message display

- [ ] T021 [US1] Integrate `CaptureService` with UI in `src/ui/main_window.py`
  - Bind space bar to `capture_and_save()`
  - Display visual feedback on capture
  - Handle errors gracefully

- [ ] T022 [US1] Add logging for User Story 1 operations in `src/lib/logging_utils.py`
  - Log capture events with timestamps
  - Log file save operations
  - Log errors with context

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Monitor Folder and Trigger ComfyUI Workflow (Priority: P1)

**Goal**: Monitor output folder and automatically trigger ComfyUI processing

**Independent Test**: Capture an image, verify application detects new file, confirms ComfyUI API connection, shows visual feedback that processing has started

### Tests for User Story 2 (TDD - Write FIRST) ⚠️

- [ ] T023 [P] [US2] Contract test for `IFileMonitorService` in `tests/contract/test_file_monitor_service.py`
  - `test_start_monitoring_success`: Verify monitoring starts without errors
  - `test_file_detected`: Verify callback is called when new file is created
  - `test_stop_monitoring`: Verify monitoring stops cleanly
  - `test_multiple_files`: Verify all files are detected in sequence

- [ ] T024 [P] [US2] Contract test for `ComfyUIService` in `tests/contract/test_comfyui_service.py`
  - `test_trigger_workflow_success`: Verify workflow is triggered successfully
  - `test_check_status`: Verify status check returns correct information
  - `test_api_unavailable`: Verify APIConnectionError when ComfyUI is down
  - `test_timeout`: Verify TimeoutError when request exceeds timeout

- [ ] T025 [P] [US2] Contract test for `CaptureQueue` in `tests/contract/test_capture_queue.py`
  - `test_enqueue_dequeue`: Verify items are processed in FIFO order
  - `test_queue_size`: Verify queue size updates correctly
  - `test_state_transitions`: Verify state transitions are correct
  - `test_empty_queue`: Verify dequeue returns None when queue is empty
  - `test_concurrent_enqueue`: Verify queue handles concurrent captures without data corruption

- [ ] T026 [P] [US2] Integration test for folder monitoring workflow in `tests/integration/test_user_story_2.py`
  - `test_folder_monitoring`: Verify new file detection triggers processing
  - `test_comfyui_integration`: Verify ComfyUI API communication
  - `test_queue_processing`: Verify multiple captures are processed in sequence
  - `test_api_unavailable_error`: Verify error handling when ComfyUI is down

### Implementation for User Story 2

- [ ] T027 [P] [US2] Create `FileMonitorServiceImpl` in `src/services/file_monitor_impl.py`
  - Implements `IFileMonitorService` using watchdog
  - Filters for JPEG files only
  - Uses `FileUtils.wait_for_file_ready()` to handle race conditions

- [ ] T028 [P] [US2] Create `ComfyUIService` in `src/services/comfyui_service_impl.py`
  - Implements `IComfyUIService` using requests library
  - Methods: `trigger_workflow()`, `check_status()`, `is_available()`
  - Default endpoint: `http://127.0.0.1:8188`

- [ ] T029 [P] [US2] Create `CaptureQueue` in `src/services/capture_queue_impl.py`
  - Implements `ICaptureQueue` with thread-safe queue
  - FIFO processing order
  - State management: `idle`, `processing`, `completed`, `error`
  - Concurrent capture handling: verify no data corruption under load

- [ ] T030 [US2] Implement `ProcessingOrchestrator` in `src/services/processing_orchestrator.py`
  - Dependencies: `IFileMonitorService`, `ICaptureQueue`, `IComfyUIService`
  - Methods: `start()`, `stop()`, `on_file_created(filepath)`
  - Coordinates file monitoring, queue management, and ComfyUI API calls
  - Queue ordering: verify sequential processing under concurrent capture load

- [ ] T031 [US2] Integrate `ProcessingOrchestrator` with UI in `src/ui/main_window.py`
  - Display processing status
  - Show visual feedback for processing start/completion/error

- [ ] T032 [US2] Add logging for User Story 2 operations in `src/lib/logging_utils.py`
  - Log file detection events
  - Log ComfyUI API calls
  - Log queue operations

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4.5: TDD Enforcement Checkpoint

**Purpose**: Verify all contract and integration tests for User Story 2 pass before implementation begins

**⚠️ CRITICAL**: No implementation tasks can begin until all tests in this checkpoint pass

- [ ] T032A [P] [US2] Verify all contract tests for `IFileMonitorService` pass
- [ ] T032B [P] [US2] Verify all contract tests for `IComfyUIService` pass
- [ ] T032C [P] [US2] Verify all contract tests for `CaptureQueue` pass
- [ ] T032D [P] [US2] Verify all integration tests for User Story 2 pass

---

## Phase 5: User Story 3 - Settings and Configuration (Priority: P2)

**Goal**: Allow users to configure output folder, ComfyUI endpoint, and workflow JSON

**Independent Test**: Open settings dialog, change output folder, verify new captures go to new folder; change ComfyUI endpoint, verify connection test works

### Tests for User Story 3 (TDD - Write FIRST) ⚠️

- [ ] T033 [P] [US3] Unit test for `ApplicationSettings` in `tests/unit/test_application_settings.py`
  - `test_valid_settings`: Verify valid settings pass validation
  - `test_invalid_folder`: Verify FolderNotFoundError for non-existent folder
  - `test_invalid_url`: Verify ValueError for invalid URL
  - `test_persistence`: Verify settings save/load correctly

- [ ] T034 [P] [US3] Integration test for settings workflow in `tests/integration/test_user_story_3.py`
  - `test_settings_persistence`: Verify settings persist across restarts
  - `test_connection_test`: Verify ComfyUI connection test works
  - `test_workflow_validation`: Verify workflow JSON validation

### Implementation for User Story 3

- [ ] T035 [P] [US3] Create `SettingsService` in `src/services/settings_service.py`
  - Methods: `load_settings()`, `save_settings()`, `validate_settings()`, `test_connection()`
  - Uses `ApplicationSettings` model for data

- [ ] T036 [P] [US3] Create settings dialog UI in `src/ui/settings_dialog.py`
  - Output folder selection (file picker)
  - ComfyUI endpoint input
  - Workflow JSON file selection
  - Connection test button
  - Save/Cancel buttons

- [ ] T037 [US3] Integrate settings dialog with main window in `src/ui/main_window.py`
  - Settings menu item opens dialog
  - Apply settings on save
  - Validate before applying

- [ ] T038 [US3] Add logging for User Story 3 operations in `src/lib/logging_utils.py`
  - Log settings changes
  - Log connection test results

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Error Handling and Recovery (Priority: P2)

**Goal**: Graceful error handling with user-friendly messages and recovery actions

**Independent Test**: Simulate each error condition, verify appropriate error message displays with recovery action

### Tests for User Story 4 (TDD - Write FIRST) ⚠️

- [ ] T039 [P] [US4] Unit test for `ErrorManager` in `tests/unit/test_error_manager.py`
  - `test_webcam_not_found`: Verify correct error message and recovery action
  - `test_api_connection_error`: Verify correct error message and recovery action
  - `test_timeout_error`: Verify correct error message and recovery action
  - `test_folder_inaccessible`: Verify correct error message and recovery action
  - `test_api_error`: Verify correct error message and recovery action

- [ ] T040 [P] [US4] Integration test for error scenarios in `tests/integration/test_user_story_4.py`
  - `test_no_webcam_scenario`: Verify error handling when no webcam
  - `test_comfyui_unavailable`: Verify error handling when ComfyUI down
  - `test_folder_inaccessible`: Verify error handling when folder inaccessible
  - `test_queue_overflow`: Verify error handling when queue full
  - `test_large_file_error`: Verify error handling for files exceeding 5MB limit
  - `test_multiple_instances_warning`: Verify warning when multiple instances detected
  - `test_workflow_error`: Verify error handling for ComfyUI workflow failures

### Implementation for User Story 4

- [ ] T042 [P] [US4] Update `CaptureService` with error handling in `src/services/capture_service.py`
  - Catch `WebcamNotFoundError`, `WebcamAccessError`, `CaptureError`
  - Display user-friendly messages via `VisualFeedback`

- [ ] T043 [P] [US4] Update `ProcessingOrchestrator` with error handling in `src/services/processing_orchestrator.py`
  - Catch `APIConnectionError`, `APIError`, `TimeoutError`
  - Queue error state management
  - Retry logic for transient failures

- [ ] T044 [US4] Update UI error display in `src/ui/main_window.py`
  - Error dialog with message and recovery action
  - Non-blocking error notifications

- [ ] T045 [US4] Add logging for User Story 4 operations in `src/lib/logging_utils.py`
  - Log all errors with full context
  - Log recovery actions

**Checkpoint**: All user stories should now be independently functional with robust error handling

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 [P] Documentation updates in docs/
  - Update README.md with feature description
  - Update quickstart.md with final configuration steps
  - Add API documentation for services

- [ ] T047 [P] Code cleanup and refactoring
  - Remove debug print statements
  - Consolidate duplicate code
  - Ensure consistent naming conventions

- [ ] T048 [P] Performance optimization across all stories
  - Optimize video capture frame rate
  - Optimize file monitoring for low CPU usage
  - Optimize ComfyUI API calls with connection pooling

- [ ] T049 [P] Additional unit tests in `tests/unit/`
  - Test all utility functions
  - Test edge cases in models
  - Test error handling paths

- [ ] T050 [P] Security hardening
  - Validate all user inputs
  - Sanitize file paths
  - Handle sensitive data (API keys if added later)

- [ ] T051 [P] Run quickstart.md validation
  - Verify installation instructions work
  - Verify configuration steps work
  - Verify troubleshooting section covers common issues

- [ ] T052 [P] Final integration test in `tests/integration/test_full_workflow.py`
  - `test_full_workflow`: Verify complete capture → save → monitor → process workflow
  - `test_error_recovery`: Verify system recovers from errors gracefully
  - `test_concurrent_captures`: Verify queue handles multiple captures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Depends on US1 for file capture
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Enhances US1, US2, US3

### TDD Enforcement Checkpoints

- **Phase 3.5**: All User Story 1 contract/integration tests MUST pass before User Story 1 implementation begins
- **Phase 4.5**: All User Story 2 contract/integration tests MUST pass before User Story 2 implementation begins
- **Phase 5.5**: All User Story 3 contract/integration tests MUST pass before User Story 3 implementation begins
- **Phase 6.5**: All User Story 4 contract/integration tests MUST pass before User Story 4 implementation begins

**⚠️ CRITICAL**: Each checkpoint must be verified before proceeding to implementation. Tests written FIRST, then implementation.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before UI integration
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (TDD):
Task: "Contract test for IWebcamService in tests/contract/test_webcam_service.py"
Task: "Contract test for CaptureService in tests/contract/test_capture_service.py"
Task: "Integration test for full capture workflow in tests/integration/test_user_story_1.py"

# Launch all models for User Story 1 together:
Task: "Create CaptureService in src/services/capture_service.py"
Task: "Create WebcamServiceImpl in src/services/webcam_impl.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence