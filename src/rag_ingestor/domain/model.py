"""
Domain models for the RAG ingestor service.

This module defines the core domain entities and value objects used throughout
the RAG ingestor system. These models represent the fundamental business concepts
and enforce domain invariants and business rules.
"""

from uuid import UUID, uuid4
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class ContentId:
    """Value object representing a unique identifier for content.

    ContentId is an immutable value object that wraps a UUID to provide
    type safety and domain semantics for content identifiers.

    Attributes:
        value: The underlying UUID value
    """

    value: UUID

    def __init__(self, value: Optional[UUID] = None):
        """Initialize a ContentId with an optional UUID.

        Args:
            value: An existing UUID to use. If None, a new UUID is generated.
        """
        self.value = value or uuid4()

    def __str__(self) -> str:
        """String representation of the ContentId.

        Returns:
            The string representation of the underlying UUID.
        """
        return str(self.value)


@dataclass
class ContentMetadata:
    """Value object for content metadata.

    ContentMetadata stores descriptive information about a piece of content,
    including its source, creation date, and other attributes.

    Attributes:
        source: The origin of the content (e.g., filename, URL)
        source_id: An identifier from the source system
        created_at: When the content was created
        modified_at: When the content was last modified
        content_type: The MIME type or format of the content
        language: The language code (e.g., 'en', 'es')
        author: The content creator
        title: The content title
        custom_metadata: Additional key-value pairs for extensibility
    """

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
        """Convert metadata to dictionary format for serialization.

        Returns:
            A dictionary containing all non-None metadata fields.
        """
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
        # Include any custom metadata fields
        result.update(self.custom_metadata)
        # Filter out None values for cleaner output
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentMetadata":
        """Create metadata from dictionary.

        This factory method reconstructs a ContentMetadata object from
        a dictionary, typically used for deserialization.

        Args:
            data: Dictionary containing metadata fields

        Returns:
            A new ContentMetadata instance
        """
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

        # Convert ISO date strings back to datetime objects
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
    """Domain entity representing a piece of content to be processed.

    Content is the primary domain entity that represents a document or text
    that has been loaded into the system and is ready for processing.

    Attributes:
        id: Unique identifier for this content
        text: The actual content text
        metadata: Associated metadata for this content
    """

    id: ContentId
    text: str
    metadata: ContentMetadata

    def __init__(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        id: Optional[ContentId] = None,
    ):
        """Initialize a Content entity.

        Args:
            text: The actual content text
            metadata: Dictionary of metadata or None
            id: Optional ContentId (generated if not provided)
        """
        self.id = id or ContentId()
        self.text = text
        self.metadata = (
            ContentMetadata.from_dict(metadata) if metadata else ContentMetadata()
        )


@dataclass
class ContentChunk:
    """Domain entity representing a chunk of processed content.

    ContentChunk represents a segment of a larger Content entity that has been
    split for more effective processing and embedding. Multiple chunks form
    a complete piece of content.

    Attributes:
        id: Unique identifier for this chunk
        content_id: Reference to the parent Content entity
        text: The text content of this chunk
        metadata: Associated metadata for this chunk
        sequence_number: The position of this chunk in the sequence
    """

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
        """Initialize a ContentChunk entity.

        Args:
            text: The text content of this chunk
            content_id: Reference to the parent Content entity
            sequence_number: The position of this chunk in the sequence
            metadata: Dictionary of metadata or None
            id: Optional ContentId (generated if not provided)
        """
        self.id = id or ContentId()
        self.content_id = content_id
        self.text = text
        self.sequence_number = sequence_number

        # Set up metadata, either from dict or existing ContentMetadata
        chunk_metadata = metadata or {}
        if not isinstance(chunk_metadata, ContentMetadata):
            chunk_metadata = ContentMetadata.from_dict(chunk_metadata)
        self.metadata = chunk_metadata

        # Always add chunk-specific metadata
        self.metadata.custom_metadata["chunk_index"] = sequence_number
        self.metadata.custom_metadata["parent_content_id"] = str(content_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary format for serialization.

        Returns:
            A dictionary representation of this chunk
        """
        return {
            "id": str(self.id),
            "content_id": str(self.content_id),
            "text": self.text,
            "sequence_number": self.sequence_number,
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentChunk":
        """Create chunk from dictionary.

        This factory method reconstructs a ContentChunk object from
        a dictionary, typically used for deserialization.

        Args:
            data: Dictionary containing chunk fields

        Returns:
            A new ContentChunk instance
        """
        return cls(
            text=data["text"],
            content_id=ContentId(UUID(data["content_id"])),
            sequence_number=data["sequence_number"],
            metadata=data.get("metadata"),
            id=ContentId(UUID(data["id"])) if "id" in data else None,
        )
