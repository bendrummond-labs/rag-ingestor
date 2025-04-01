from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

# Define supported file types
_SUPPORTED_EXTENSIONS = {
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.csv': 'text/csv',
    # Add more supported file types as needed
}

def supported_file_types():
    """Return a list of supported file extensions"""
    return list(_SUPPORTED_EXTENSIONS.keys())

def detect_file_type(filename):
    """
    Detect file type from filename
    
    Args:
        filename (str): Name of the file
        
    Returns:
        str: Mime type of the file
        
    Raises:
        ValueError: If file type is not supported
    """
    ext = os.path.splitext(filename.lower())[1]
    if ext not in _SUPPORTED_EXTENSIONS:
        supported = ", ".join(supported_file_types())
        raise ValueError(f"Unsupported file type: {ext}. Supported types are: {supported}")
    
    return _SUPPORTED_EXTENSIONS[ext]

def load_text_file(path: str) -> str:
    """
    Load text from a file
    
    Args:
        path (str): Path to the file
        
    Returns:
        str: Content of the file
        
    Raises:
        FileNotFoundError: If file does not exist
        UnicodeDecodeError: If file cannot be decoded as UTF-8
    """
    file_path = Path(path)
    
    if not file_path.exists():
        logger.error(f"File not found: {path}")
        raise FileNotFoundError(f"File {path} not found.")
    
    logger.info(f"Loading file: {path}")
    try:
        content = file_path.read_text(encoding='utf-8')
        logger.info(f"Successfully loaded {len(content)} characters from {path}")
        return content
    except UnicodeDecodeError as e:
        logger.error(f"Failed to decode file {path} as UTF-8")
        raise