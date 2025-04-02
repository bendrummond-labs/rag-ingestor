from langchain_community.document_loaders import CSVLoader
from rag_ingestor.adapters.loaders.base import register_loader


@register_loader(".csv")
def load_csv_file(path: str):
    return CSVLoader(path).load()
