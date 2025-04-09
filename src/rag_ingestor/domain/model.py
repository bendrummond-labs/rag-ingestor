from uuid import UUID, uuid4
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class ContentId:
    """Value object representing a unique identifier for content."""

    value: UUID

    def __init__(self, value: Optional[UUID] = None):
        self.value = value or uuid4()

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class ContentMetadata:
    """Value object for content metadata."""

    source: Optional[str] = None
    source_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: Optional[datetime] = None
    content_type: Optional[str] = None
    language: Optional[str] = None
    author: Optional[str] = None
    title: Optional[str] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary format."""
        result = {
            "source": self.source,
            "source_id": self.source_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "content_type": self.content_type,
            "language": self.language,
            "author": self.author,
            "title": self.title,
        }
        result.update(self.custom_metadata)
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentMetadata":
        """Create metadata from dictionary."""
        # Extract known fields
        known_fields = {
            "source",
            "source_id",
            "created_at",
            "modified_at",
            "content_type",
            "language",
            "author",
            "title",
        }
        base_data = {k: data.get(k) for k in known_fields if k in data}

        # Convert ISO date strings back to datetime
        for date_field in ["created_at", "modified_at"]:
            if date_field in base_data and isinstance(base_data[date_field], str):
                try:
                    base_data[date_field] = datetime.fromisoformat(
                        base_data[date_field]
                    )
                except ValueError:
                    base_data[date_field] = None

        # Everything else goes into custom_metadata
        custom_metadata = {k: v for k, v in data.items() if k not in known_fields}

        return cls(**base_data, custom_metadata=custom_metadata)


@dataclass
class Content:
    """Domain entity representing a piece of content to be processed."""

    id: ContentId
    text: str
    metadata: ContentMetadata

    def __init__(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        id: Optional[ContentId] = None,
    ):
        self.id = id or ContentId()
        self.text = text
        self.metadata = (
            ContentMetadata.from_dict(metadata) if metadata else ContentMetadata()
        )


# src/rag_ingestor/domain/model.py (to be added)
@dataclass
class ContentChunk:
    """Domain entity representing a chunk of processed content."""

    id: ContentId
    content_id: ContentId
    text: str
    metadata: ContentMetadata
    sequence_number: int

    def __init__(
        self,
        text: str,
        content_id: ContentId,
        sequence_number: int,
        metadata: Optional[Dict[str, Any]] = None,
        id: Optional[ContentId] = None,
    ):
        self.id = id or ContentId()
        self.content_id = content_id
        self.text = text
        self.sequence_number = sequence_number

        chunk_metadata = metadata or {}
        if not isinstance(chunk_metadata, ContentMetadata):
            chunk_metadata = ContentMetadata.from_dict(chunk_metadata)
        self.metadata = chunk_metadata

        self.metadata.custom_metadata["chunk_index"] = sequence_number
        self.metadata.custom_metadata["parent_content_id"] = str(content_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary format for serialization."""
        return {
            "id": str(self.id),
            "content_id": str(self.content_id),
            "text": self.text,
            "sequence_number": self.sequence_number,
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentChunk":
        """Create chunk from dictionary."""
        return cls(
            text=data["text"],
            content_id=ContentId(UUID(data["content_id"])),
            sequence_number=data["sequence_number"],
            metadata=data.get("metadata"),
            id=ContentId(UUID(data["id"])) if "id" in data else None,
        )
