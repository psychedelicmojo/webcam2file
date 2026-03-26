"""Contract tests for ICaptureQueue interface."""

import threading
from typing import Optional

from src.services.capture_queue import (
    ICaptureQueue,
    ProcessingState,
)


class MockCaptureQueue(ICaptureQueue):
    """Mock implementation of ICaptureQueue for testing."""

    def __init__(self):
        self._queue = []
        self._processing_state = ProcessingState.IDLE
        self._error_message = None

    def enqueue(self, image_path: str) -> None:
        """Add an image to the processing queue."""
        self._queue.append(image_path)

    def dequeue(self) -> Optional[str]:
        """Remove and return the next image from the queue."""
        if not self._queue:
            return None
        return self._queue.pop(0)

    def get_queue_size(self) -> int:
        """Get the current queue size."""
        return len(self._queue)

    def get_processing_state(self) -> ProcessingState:
        """Get the current processing state."""
        return self._processing_state

    def set_processing_state(
        self,
        state: ProcessingState,
        error_message: Optional[str] = None
    ) -> None:
        """Set the current processing state."""
        self._processing_state = state
        self._error_message = error_message

    def is_processing(self) -> bool:
        """Check if processing is currently active."""
        return self._processing_state == ProcessingState.PROCESSING


class TestCaptureQueueContract:
    """Contract tests for ICaptureQueue interface."""

    def test_enqueue_dequeue(self):
        """Verify items are processed in FIFO order."""
        queue = MockCaptureQueue()

        # Enqueue items
        queue.enqueue("/path/to/image1.jpg")
        queue.enqueue("/path/to/image2.jpg")
        queue.enqueue("/path/to/image3.jpg")

        # Verify FIFO order
        assert queue.dequeue() == "/path/to/image1.jpg"
        assert queue.dequeue() == "/path/to/image2.jpg"
        assert queue.dequeue() == "/path/to/image3.jpg"

    def test_queue_size(self):
        """Verify queue size updates correctly."""
        queue = MockCaptureQueue()

        assert queue.get_queue_size() == 0

        queue.enqueue("/path/to/image1.jpg")
        assert queue.get_queue_size() == 1

        queue.enqueue("/path/to/image2.jpg")
        assert queue.get_queue_size() == 2

        queue.dequeue()
        assert queue.get_queue_size() == 1

    def test_state_transitions(self):
        """Verify state transitions are correct."""
        queue = MockCaptureQueue()

        # Initial state
        assert queue.get_processing_state() == ProcessingState.IDLE

        # Transition to processing
        queue.set_processing_state(ProcessingState.PROCESSING)
        assert queue.get_processing_state() == ProcessingState.PROCESSING

        # Transition to completed
        queue.set_processing_state(ProcessingState.COMPLETED)
        assert queue.get_processing_state() == ProcessingState.COMPLETED

        # Transition to error with message
        queue.set_processing_state(ProcessingState.ERROR, "Test error")
        assert queue.get_processing_state() == ProcessingState.ERROR

    def test_empty_queue(self):
        """Verify dequeue returns None when queue is empty."""
        queue = MockCaptureQueue()

        assert queue.dequeue() is None

    def test_concurrent_enqueue(self):
        """Verify queue handles concurrent captures without data corruption."""
        queue = MockCaptureQueue()
        num_threads = 10
        items_per_thread = 100
        errors = []

        def enqueue_items(thread_id):
            try:
                for i in range(items_per_thread):
                    queue.enqueue(f"/path/to/image_{thread_id}_{i}.jpg")
            except Exception as e:
                errors.append(e)

        # Launch concurrent threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=enqueue_items, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0

        # Verify all items were enqueued
        expected_total = num_threads * items_per_thread
        assert queue.get_queue_size() == expected_total

        # Verify FIFO order by dequeuing all items
        dequeued_items = []
        while queue.get_queue_size() > 0:
            item = queue.dequeue()
            dequeued_items.append(item)

        assert len(dequeued_items) == expected_total

        # Verify all items are unique
        assert len(set(dequeued_items)) == expected_total
