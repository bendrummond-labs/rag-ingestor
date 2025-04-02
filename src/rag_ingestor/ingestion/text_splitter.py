from typing import List, Type, Dict, Any
import logging
from enum import Enum

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    MarkdownTextSplitter,
    PythonCodeTextSplitter,
    LatexTextSplitter,
    HTMLSectionSplitter,
    TokenTextSplitter,
)
from langchain_text_splitters.base import TextSplitter

logger = logging.getLogger(__name__)


class SplitterType(str, Enum):
    """Supported text splitter types"""

    RECURSIVE = "recursive"
    CHARACTER = "character"
    MARKDOWN = "markdown"
    PYTHON = "python"
    LATEX = "latex"
    HTML = "html"
    TOKEN = "token"


SPLITTER_REGISTRY: Dict[SplitterType, Type[TextSplitter]] = {
    SplitterType.RECURSIVE: RecursiveCharacterTextSplitter,
    SplitterType.CHARACTER: CharacterTextSplitter,
    SplitterType.MARKDOWN: MarkdownTextSplitter,
    SplitterType.PYTHON: PythonCodeTextSplitter,
    SplitterType.LATEX: LatexTextSplitter,
    SplitterType.HTML: HTMLSectionSplitter,
    SplitterType.TOKEN: TokenTextSplitter,
}

DEFAULT_PARAMS: Dict[SplitterType, Dict[str, Any]] = {
    SplitterType.RECURSIVE: {"separators": ["\n\n", "\n", ". ", " ", ""]},
    SplitterType.HTML: {
        "headers_to_split_on": [
            ("h1", 5),
            ("h2", 4),
            ("h3", 3),
            ("h4", 2),
        ]
    },
    SplitterType.TOKEN: {"encoding_name": "cl100k_base"},
}


def get_text_splitter(
    splitter_type: SplitterType = SplitterType.RECURSIVE,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    **kwargs,
) -> TextSplitter:
    splitter_class = SPLITTER_REGISTRY.get(splitter_type)
    if not splitter_class:
        logger.warning(
            f"Unknown splitter type: {splitter_type}, falling back to RecursiveCharacterTextSplitter"
        )
        splitter_class = RecursiveCharacterTextSplitter
        splitter_type = SplitterType.RECURSIVE

    # Merge default parameters with provided kwargs
    params = DEFAULT_PARAMS.get(splitter_type, {}).copy()
    params.update(kwargs)

    # Common parameters for all splitters
    params["chunk_size"] = chunk_size
    params["chunk_overlap"] = chunk_overlap

    try:
        # Instantiate the splitter with the merged parameters
        splitter = splitter_class(**params)
        return splitter
    except Exception as e:
        logger.error(f"Failed to create text splitter: {str(e)}")
        # Fall back to RecursiveCharacterTextSplitter with basic params
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )


def split_text(
    text: str,
    splitter_type: SplitterType = SplitterType.RECURSIVE,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    **kwargs,
) -> List[str]:
    """
    Split text using the specified splitter type

    Args:
        text: Text to be split
        splitter_type: Type of splitter to use
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between consecutive chunks
        **kwargs: Additional parameters for the specific splitter

    Returns:
        List of text chunks
    """
    if not text:
        logger.warning("Empty text provided for splitting")
        return []

    logger.info(
        f"Splitting text of length {len(text)} with {splitter_type} splitter, "
        f"chunk_size={chunk_size}, chunk_overlap={chunk_overlap}"
    )

    # Get the appropriate text splitter
    splitter = get_text_splitter(
        splitter_type=splitter_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs,
    )

    # Split the text
    chunks = splitter.split_text(text)

    # Log statistics
    if chunks:
        avg_chunk_length = sum(len(chunk) for chunk in chunks) / len(chunks)
        min_chunk_length = min(len(chunk) for chunk in chunks)
        max_chunk_length = max(len(chunk) for chunk in chunks)
        logger.debug(
            f"Text split into {len(chunks)} chunks - "
            f"avg: {avg_chunk_length:.1f}, min: {min_chunk_length}, max: {max_chunk_length}"
        )

    return chunks
