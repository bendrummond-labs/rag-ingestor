"""
Application services for document processing in the RAG ingestor.

This module provides the application service layer that orchestrates
domain operations and interfaces with external systems. It contains
services that implement use cases for document ingestion, processing,
and management.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException

from rag_ingestor.domain.model import Content, ContentChunk
from rag_ingestor.ports.outbound.content_loader_port import ContentLoaderPort
from rag_ingestor.ports.outbound.text_chunking_port import TextChunkingPort

# Set up logging
logger = logging.getLogger(__name__)


class DocumentService:
    """
    Service responsible for document processing operations.

    This service acts as the primary orchestrator for document-related use cases.
    It coordinates between the API layer and the domain layer, delegating to the
    appropriate ports for specific operations like document loading.

    Attributes:
        document_loader: A port implementation for loading documents
    """

    def __init__(
        self,
        document_loader: ContentLoaderPort,
        text_chunker: Optional[TextChunkingPort],
    ):
        """
        Initialize the document service with required dependencies.

        Args:
            document_loader: Implementation of the ContentLoaderPort
        """
        self.document_loader = document_loader
        self.text_chunker = text_chunker

    def get_supported_extensions(self) -> List[str]:
        """
        Get a list of supported file extensions.

        This method queries the document loader for the file extensions
        it supports for ingestion.

        Returns:
            List of supported file extensions (e.g., ['.txt', '.pdf'])
        """
        return list(getattr(self.document_loader, "loaders", {}).keys())

    async def process_document(
        self,
        file: UploadFile,
        temp_file_path: Path,
        chunk_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process an uploaded document file.

        This method handles the complete document processing workflow:
        1. Validates the file type
        2. Loads the document content
        3. Prepares a summary of the processing results

        Args:
            file: The uploaded file metadata
            temp_file_path: Path to the temporary file on disk

        Returns:
            Dictionary containing processing results and statistics

        Raises:
            HTTPException: If file validation fails or processing encounters an error
        """
        logger.info(f"Processing file: {file.filename}")

        try:
            self._validate_file_extension(file.filename)

            contents: List[Content] = self._load_document_content(temp_file_path)

            chunks: List[ContentChunk] = []
            if self.text_chunker:
                for content in contents:
                    content_chunks = self.text_chunker.chunk_content(
                        content, chunk_params
                    )
                    chunks.extend(content_chunks)

                logger.info(
                    f"Created {len(chunks)} chunks from {len(contents)} content items"
                )

            result = self._create_processing_summary(file.filename, contents, chunks)

            return result

        except HTTPException:
            # Re-raise HTTP exceptions without wrapping them
            raise
        except Exception as e:
            # Log and wrap other exceptions
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Error processing document: {str(e)}"
            )

    def _validate_file_extension(self, filename: str) -> None:
        """
        Validate that the file has a supported extension.

        Args:
            filename: Name of the file to validate

        Raises:
            HTTPException: If the file extension is missing or unsupported
        """
        file_extension = os.path.splitext(filename)[1].lower()

        if not file_extension:
            raise HTTPException(
                status_code=400, detail="File does not have a valid extension."
            )

        supported_extensions = self.get_supported_extensions()
        if file_extension not in supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Supported types are: {supported_extensions}",
            )

    def _load_document_content(self, file_path: Path) -> List[Content]:
        """
        Load document content from a file path.

        Args:
            file_path: Path to the document file

        Returns:
            List of Content entities extracted from the document
        """
        return self.document_loader.load_content(file_path)

    def _create_processing_summary(
        self, filename: str, contents: List[Content], chunks: List[ContentChunk] = None
    ) -> Dict[str, Any]:
        """
        Create a summary of document processing results.

        Args:
            filename: Name of the processed file
            contents: List of Content entities extracted from the document
            chunks: Optional list of ContentChunk entities

        Returns:
            Dictionary containing processing statistics and information
        """
        summary = {
            "status": "success",
            "filename": filename,
            "content_count": len(contents),
            "total_characters": sum(len(content.text) for content in contents),
        }

        if chunks:
            summary.update(
                {
                    "chunk_count": len(chunks),
                    "chunks": [
                        {
                            "chunk_id": str(chunk.id),
                            "sequence_number": chunk.sequence_number,
                            "chars": len(chunk.text),
                        }
                        for chunk in chunks[:5]
                    ],
                    "average_chunk_size": (
                        sum(len(chunk.text) for chunk in chunks) / len(chunks)
                        if chunks
                        else 0
                    ),
                }
            )

            if len(chunks) > 5:
                summary["chunks"].append(
                    {"note": f"...and {len(chunks) - 5} more chunks"}
                )

        return summary
