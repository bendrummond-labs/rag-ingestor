from langchain_community.document_loaders import UnstructuredPDFLoader
from rag_ingestor.ingestion.file_loader import register_loader


@register_loader(".pdf")
def load_pdf_file(path: str):
    return UnstructuredPDFLoader(path).load()
