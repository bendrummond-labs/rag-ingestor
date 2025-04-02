import os
import tempfile
import logging
from typing import List, Dict
from fastapi import HTTPException, status, UploadFile
from pathlib import Path

from langchain_core.documents import Document

from rag_ingestor.adapters.loaders.loader_manager import LoaderManager
from rag_ingestor.adapters.splitters.splitter_manager import SplitterManager
from rag_ingestor.config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(
        self, loader_manager: LoaderManager, splitter_manager: SplitterManager
    ):
        """
        Initialize the document service

        Args:
            loader_manager: Manager for document loaders
        """
        self.loader_manager = loader_manager
        self.splitter_manager = splitter_manager

    def validate_file_type(self, ext: str):
        """
        Validate the file type based on its extension.
        """
        if not self.loader_manager.get_loader(ext):
            supported = ", ".join(self.loader_manager.loaders.keys())
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {ext}. Supported: {supported}",
            )

    def validate_chunking_parameters(self, chunk_size: int, chunk_overlap: int):
        """
        Validate the chunking parameters.
        """
        if chunk_overlap >= chunk_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="chunk_overlap must be less than chunk_size",
            )

    def read_file_contents(self, file: UploadFile) -> bytes:
        size, contents = 0, b""
        while True:
            chunk = file.file.read(1024)
            if not chunk:
                break
            size += len(chunk)
            contents += chunk

            if size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Max allowed is {settings.MAX_FILE_SIZE} bytes.",
                )

        file.file.seek(0)
        return contents

    def load_document(self, contents: bytes, file_extension: str) -> List[Document]:
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=file_extension
            ) as temp_file:
                temp_file.write(contents)
                temp_path = temp_file.name

                logger.info(f"Loading document with {file_extension} loader")
                return self.loader_manager.load_document(temp_path)

        except Exception as e:
            logger.exception(f"Error loading document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error loading document: {e}",
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logger.warning(f"Error removing temp file {temp_path}: {e}")

    def split_document(
        self,
        documents: List[Document],
        splitter_type: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[Dict]:

        try:
            splitter = self.splitter_manager.get_splitter(
                splitter_type, chunk_size, chunk_overlap
            )
            chunks = splitter.split_documents(documents)
            return [
                {
                    "page_content": doc.page_content,
                    "metadata": doc.metadata,
                }
                for doc in chunks
            ]
        except ValueError as e:
            logger.exception(f"Invalid splitter configurations: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid splitter configuration: {str(e)}",
            )
        except Exception as e:
            logger.exception(f"Error splitting document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error splitting document: {str(e)}",
            )

    async def process_document(
        self, file: UploadFile, splitter_type: str, chunk_size: int, chunk_overlap: int
    ) -> List[Dict]:

        file_ext = Path(file.filename).suffix.lower()

        self.validate_file_type(file_ext)
        self.validate_chunking_parameters(chunk_size, chunk_overlap)

        contents = self.read_file_contents(file)
        logger.info(f"File read: {file.filename}, size={len(contents)} bytes")

        documents = self.load_document(contents, file_ext)

        chunks = self.split_document(
            documents, splitter_type, chunk_size, chunk_overlap
        )
        logger.info(f"Split into {len(chunks)} chunks")

        return chunks
