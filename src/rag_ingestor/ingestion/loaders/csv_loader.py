from langchain_community.document_loaders import CSVLoader
from rag_ingestor.ingestion.file_loader import register_loader


@register_loader(".csv")
def load_csv_file(path: str):
    return CSVLoader(path).load()
