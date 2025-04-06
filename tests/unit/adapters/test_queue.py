import pytest

from rag_ingestor.adapters.queue.memory import InMemoryMessageQueue


@pytest.mark.asyncio
class TestInMemoryMessageQueue:
    """Tests for the InMemoryMessageQueue class."""

    async def test_initialize(self):
        """Test initializing the queue."""
        queue = InMemoryMessageQueue()

        # Verify initial state
        assert not queue.initialized
        assert queue.queues == {}

        # Initialize the queue
        await queue.initialize()

        # Verify state after initialization
        assert queue.initialized

    async def test_shutdown(self):
        """Test shutting down the queue."""
        queue = InMemoryMessageQueue()
        await queue.initialize()

        # Add some test data
        queue.queues = {"test-queue": [{"message": "test"}]}

        # Shutdown the queue
        await queue.shutdown()

        # Verify state after shutdown
        assert not queue.initialized
        assert queue.queues == {}

    async def test_send_message(self):
        """Test sending a message to the queue."""
        queue = InMemoryMessageQueue()
        await queue.initialize()

        # Send a message
        result = await queue.send_message("test-queue", {"data": "test-data"})

        # Verify the result
        assert result is True

        # Verify the message was stored
        assert "test-queue" in queue.queues
        assert len(queue.queues["test-queue"]) == 1
        assert queue.queues["test-queue"][0]["data"] == "test-data"

        # Verify timestamp was added
        assert "timestamp" in queue.queues["test-queue"][0]

    async def test_send_message_not_initialized(self):
        """Test sending a message when queue is not initialized."""
        queue = InMemoryMessageQueue()

        # Send a message without initializing
        result = await queue.send_message("test-queue", {"data": "test-data"})

        # Verify the result
        assert result is False

    async def test_get_messages(self):
        """Test getting messages from the queue."""
        queue = InMemoryMessageQueue()

        # Add some test data directly
        queue.queues = {"test-queue": [{"message": "test1"}, {"message": "test2"}]}

        # Get messages
        messages = queue.get_messages("test-queue")

        # Verify the result
        assert len(messages) == 2
        assert messages[0]["message"] == "test1"
        assert messages[1]["message"] == "test2"

        # Test getting messages from a non-existent queue
        messages = queue.get_messages("nonexistent-queue")
        assert messages == []
