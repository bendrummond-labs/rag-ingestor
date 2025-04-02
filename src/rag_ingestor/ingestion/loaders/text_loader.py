from langchain_community.document_loaders import TextLoader
from rag_ingestor.ingestion.file_loader import register_loader


@register_loader(".txt")
@register_loader(".md")
def load_text_file(path: str):
    return TextLoader(path, encoding="utf-8").load()
