import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException

from rag_ingestor.domain.model import Content
from rag_ingestor.ports.outbound.content_loader_port import ContentLoaderPort

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, document_loader: ContentLoaderPort):
        self.document_loader = document_loader

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return list(getattr(self.document_loader, "loaders", {}).keys())

    async def process_document(
        self, file: UploadFile, temp_file_path: Path
    ) -> Dict[str, Any]:
        """Process an uploaded document file."""
        logger.info(f"Processing file: {file.filename}")

        file_extension = os.path.splitext(file.filename)[1].lower()
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

        try:
            contents: List[Content] = self.document_loader.load_content(temp_file_path)

            return {
                "status": "success",
                "filename": file.filename,
                "content_count": len(contents),
                "total_characters": sum(len(content.text) for content in contents),
            }

        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Error processing document: {str(e)}"
            )
