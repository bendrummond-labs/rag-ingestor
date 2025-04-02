from rag_ingestor.adapters.splitters.base import (
    SPLITTER_SERVICE_REGISTRY,
    BaseSplitterService,
)


def get_splitter_service(
    splitter_type: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> BaseSplitterService:
    splitter_cls = SPLITTER_SERVICE_REGISTRY.get(splitter_type)
    if not splitter_cls:
        raise ValueError(f"Unsupported splitter type: {splitter_type}")
    return splitter_cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
