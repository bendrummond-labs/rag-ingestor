from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging

logger = logging.getLogger(__name__)

def chunk_text(text, chunk_size=500, chunk_overlap=100):
    """
    Split text into chunks using RecursiveCharacterTextSplitter
    
    Args:
        text (str): Text to be chunked
        chunk_size (int): Maximum size of each chunk
        chunk_overlap (int): Overlap between consecutive chunks
        
    Returns:
        list: List of text chunks
    """
    if not text:
        logger.warning("Empty text provided for chunking")
        return []
    
    logger.info(f"Chunking text of length {len(text)} with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = splitter.split_text(text)
    logger.info(f"Text split into {len(chunks)} chunks")
    
    # Log some statistics about chunks
    if chunks:
        avg_chunk_length = sum(len(chunk) for chunk in chunks) / len(chunks)
        min_chunk_length = min(len(chunk) for chunk in chunks)
        max_chunk_length = max(len(chunk) for chunk in chunks)
        logger.debug(f"Chunk statistics - avg: {avg_chunk_length:.1f}, min: {min_chunk_length}, max: {max_chunk_length}")
    
    return chunks