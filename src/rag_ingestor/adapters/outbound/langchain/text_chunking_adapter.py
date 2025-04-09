import logging
from typing import List, Optional, Dict, Any
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    TextSplitter,
)

from rag_ingestor.ports.outbound.text_chunking_port import TextChunkingPort
from rag_ingestor.domain.model import Content, ContentChunk

logger = logging.getLogger(__name__)


class LangchainTextChunkingAdapter(TextChunkingPort):
    RECURSIVE_CHARACTER = "recursive_character"
    TOKEN = "token"

    SPLITTER_MAPPING = {
        RECURSIVE_CHARACTER: RecursiveCharacterTextSplitter,
        TOKEN: TokenTextSplitter,
    }

    def __init__(
        self,
        splitter_type: str = RECURSIVE_CHARACTER,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        **splitter_params,
    ):
        if splitter_type not in self.SPLITTER_MAPPING:
            raise ValueError(
                f"Unsupported splitter type: {splitter_type}. "
                f"Supported types are: {list(self.SPLITTER_MAPPING.keys())}"
            )

        self.splitter_type = splitter_type
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter_params = splitter_params

        self.text_splitter = self._create_text_splitter()

        logger.info(
            f"Initialized {splitter_type} splitter with chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}"
        )

    def _create_text_splitter(self) -> TextSplitter:
        """
        Create a Langchain text splitter instance.

        Returns:
            Configured TextSplitter instance
        """
        splitter_class = self.SPLITTER_MAPPING[self.splitter_type]

        params = {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }

        params.update(self.splitter_params)

        return splitter_class(**params)

    def chunk_content(
        self, content: Content, chunk_params: Optional[Dict[str, Any]] = None
    ) -> List[ContentChunk]:

        text_splitter = self.text_splitter

        if chunk_params:
            logger.debug(f"Using custom chunk parameters: {chunk_params}")
            temp_size = chunk_params.get("chunk_size", self.chunk_size)
            temp_overlap = chunk_params.get("chunk_overlap", self.chunk_overlap)

            splitter_params = self.splitter_params.copy()

            for value, key in chunk_params.items():
                if key not in ("chunk_size", "chunk_overlap"):
                    splitter_params[key] = value

            splitter_class = self.SPLITTER_MAPPING[self.splitter_type]
            text_splitter = splitter_class(
                chunk_size=temp_size, chunk_overlap=temp_overlap, **splitter_params
            )

        try:
            text_chunks = text_splitter.split_text(content.text)
            logger.debug(f"Split content into {len(text_chunks)} chunks")
        except Exception as e:
            logger.error(f"Error chunking content: {str(e)}")
            raise

        content_chunks = []
        for i, chunk_text in enumerate(text_chunks):
            # Copy metadata from parent content
            metadata = content.metadata.to_dict()

            # Add chunk-specific metadata
            metadata.update(
                {
                    "chunk_index": i,
                    "total_chunks": len(text_chunks),
                    "parent_content_id": str(content.id),
                }
            )

            # Create the chunk
            chunk = ContentChunk(
                text=chunk_text,
                content_id=content.id,
                sequence_number=i,
                metadata=metadata,
            )

            content_chunks.append(chunk)

        return content_chunks
