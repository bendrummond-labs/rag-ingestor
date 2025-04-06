from rag_ingestor.adapters.loaders.loader_manager import LoaderManager
from rag_ingestor.adapters.loaders.text_loader import TextLoader
from rag_ingestor.adapters.loaders.pdf_loader import PDFLoader
from rag_ingestor.adapters.loaders.csv_loader import CSVLoader

from rag_ingestor.services.document_service import DocumentService
from rag_ingestor.services.ingestion_service import IngestionService
from rag_ingestor.di_container import get_message_queue


def create_loader_manager() -> LoaderManager:
    """Create and configure a loader manager with all supported loaders"""
    manager = LoaderManager()

    # Register all supported loaders
    manager.register_loader(".txt", TextLoader())
    manager.register_loader(".md", TextLoader())
    manager.register_loader(".pdf", PDFLoader())
    manager.register_loader(".csv", CSVLoader())

    return manager


def create_document_service() -> DocumentService:
    """Create a document service with all dependencies"""
    loader_manager = create_loader_manager()
    return DocumentService(loader_manager=loader_manager)


def create_ingestion_service() -> IngestionService:
    """Create and configure the ingestion service with all dependencies"""
    document_service = create_document_service()
    message_queue = get_message_queue()

    return IngestionService(
        document_service=document_service,
        message_queue=message_queue,
    )
