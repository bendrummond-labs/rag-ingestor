import logging
from typing import Dict, Any

from rag_ingestor.adapters.loaders import (
    TextLoader,
    PDFLoader,
    CSVLoader,
    LoaderManager,
)

from rag_ingestor.adapters.splitters import (
    SplitterManager,
    MarkdownSplitter,
    PlainTextSplitter,
)

from rag_ingestor.services.document_service import DocumentService
from rag_ingestor.services.ingestion_service import IngestionService
from rag_ingestor.adapters.queue.base import MessageQueue
from rag_ingestor.adapters.queue.kafka import KafkaMessageQueue
from rag_ingestor.adapters.queue.memory import InMemoryMessageQueue
from rag_ingestor.config import settings


logger = logging.getLogger(__name__)


class DIContainer:
    """Dependency Injection Container"""

    _instance = None

    @classmethod
    def get_instance(cls) -> "DIContainer":
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.services: Dict[str, Any] = {}

    def register(self, name: str, instance: Any) -> None:
        """Register a service"""
        self.services[name] = instance

    def get(self, name: str) -> Any:
        """Get a service"""
        if name not in self.services:
            raise KeyError(f"Service not registered: {name}")
        return self.services[name]

    def has(self, name: str) -> bool:
        """Check if a service is registered"""
        return name in self.services


container = DIContainer.get_instance()


async def initialize_container():
    """Initialize all dependencies in the container"""

    # 1. Create and register the LoaderManager with all loaders
    loader_manager = LoaderManager()
    loader_manager.register_loader(".txt", TextLoader())
    loader_manager.register_loader(".md", TextLoader())
    loader_manager.register_loader(".pdf", PDFLoader())
    loader_manager.register_loader(".csv", CSVLoader())
    container.register("loader_manager", loader_manager)

    # 2. Create and register the SplitterManager with all splitters
    splitter_manager = SplitterManager()
    splitter_manager.register_splitter("plain", PlainTextSplitter)
    splitter_manager.register_splitter("markdown", MarkdownSplitter)
    container.register("splitter_manager", splitter_manager)

    # 3. Create and register the message queue
    queue_type = "memory" if not settings.ENABLE_KAFKA else "kafka"
    message_queue: MessageQueue

    if queue_type == "kafka":
        message_queue = KafkaMessageQueue.get_instance()
    else:
        message_queue = InMemoryMessageQueue()

    await message_queue.initialize()
    container.register("message_queue", message_queue)

    # 4. Create and register the document service
    document_service = DocumentService(loader_manager, splitter_manager)
    container.register("document_service", document_service)

    # 5. Create and register the ingestion service
    ingestion_service = IngestionService(
        document_service=document_service,
        message_queue=message_queue,
    )
    container.register("ingestion_service", ingestion_service)

    logger.info("Dependency container initialized")


async def shutdown_container():
    """Shutdown all services in the container"""

    # Shutdown the message queue if it exists
    if container.has("message_queue"):
        message_queue = container.get("message_queue")
        await message_queue.shutdown()

    logger.info("Dependency container shutdown complete")


# Factory function to get the ingestion service
def get_ingestion_service() -> IngestionService:
    """Get the ingestion service from the container"""
    return container.get("ingestion_service")


# Factory function to get the document service
def get_document_service() -> DocumentService:
    """Get the document service from the container"""
    return container.get("document_service")


# Factory function to get the loader manager
def get_loader_manager() -> LoaderManager:
    """Get the loader manager from the container"""
    return container.get("loader_manager")


# Factory function to get the splitter manager
def get_splitter_manager() -> SplitterManager:
    """Get the splitter manager from the container"""
    return container.get("splitter_manager")


# Factory function to get the message queue
def get_message_queue() -> MessageQueue:
    """Get the message queue from the container"""
    return container.get("message_queue")
