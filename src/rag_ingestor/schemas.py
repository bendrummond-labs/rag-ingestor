from pydantic import BaseModel


class IngestRequest(BaseModel):
    file_id: str
    chunks: list[str]


class IngestResponse(BaseModel):
    status: str
    file_id: str
    num_chunks: int


class JobStatus(BaseModel):
    file_id: str
    status: str
    message: str
    num_chunks: int = 0
    chunks_processed: int = 0
