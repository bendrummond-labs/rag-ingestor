import httpx
from typing import List, Dict, Any, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from rag_ingestor.config import settings, logger


class EmbedderService:
    def __init__(
        self,
        base_url: str = settings.EMBEDDER_URL,
        timeout: float = settings.EMBEDDER_TIMEOUT,
        batch_size: int = settings.EMBEDDER_BATCH_SIZE,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.batch_size = batch_size

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def _send_request(self, payload: Dict[str, Any]) -> bool:
        """Send request to embedder with retry logic"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.base_url, json=payload)
            response.raise_for_status()
            return True

    async def embed_chunks(
        self,
        file_id: str,
        chunks: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        if not chunks:
            logger.warning(f"No chunks to embed for file ID: {file_id}")
            return True

        if metadata and len(metadata) != len(chunks):
            logger.error(
                f"Metadata length mismatch: {len(metadata)} vs {len(chunks)} chunks"
            )
            return False

        # Process in batches
        batches = [
            chunks[i : i + self.batch_size]
            for i in range(0, len(chunks), self.batch_size)
        ]
        total_batches = len(batches)

        logger.info(
            f"Processing {len(chunks)} chunks in {total_batches} batches for file ID: {file_id}"
        )

        success_count = 0
        batch_results = []

        # Process each batch
        for i, batch in enumerate(batches):
            batch_metadata = None
            if metadata:
                start_idx = i * self.batch_size
                batch_metadata = metadata[start_idx : start_idx + len(batch)]

            batch_payload = {
                "file_id": file_id,
                "chunks": batch,
                "batch_index": i,
                "total_batches": total_batches,
            }

            if batch_metadata:
                batch_payload["metadata"] = batch_metadata

            try:
                logger.info(
                    f"Sending batch {i+1}/{total_batches} to embedder for file ID: {file_id}"
                )
                result = await self._send_request(batch_payload)
                batch_results.append(result)
                if result:
                    success_count += len(batch)
                    logger.info(f"Successfully processed batch {i+1}/{total_batches}")
                else:
                    logger.error(f"Failed to process batch {i+1}/{total_batches}")
            except Exception as e:
                logger.error(f"Error processing batch {i+1}/{total_batches}: {str(e)}")
                batch_results.append(False)

        # Log completion summary
        if success_count == len(chunks):
            logger.info(f"All chunks successfully processed for file ID: {file_id}")
            return True
        else:
            logger.warning(
                f"Partial success: {success_count}/{len(chunks)} chunks processed for file ID: {file_id}"
            )
            return False


# Initialize service
embedder_service = EmbedderService()
