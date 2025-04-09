import uuid
from rag_ingestor.domain.model import Content, ContentId, ContentMetadata


def test_content_id_creation():
    id1 = ContentId()
    assert isinstance(id1.value, uuid.UUID)

    test_uuid = uuid.uuid4()
    id2 = ContentId(test_uuid)
    assert id2.value == test_uuid


def test_content_metadata_serialization():
    metadata = ContentMetadata(
        source="test_source",
        source_id="123",
        content_type="text/plain",
        language="en",
        title="Test Document",
    )

    metadata_dict = metadata.to_dict()
    assert metadata_dict["source"] == "test_source"
    assert metadata_dict["title"] == "Test Document"

    reconstructed = ContentMetadata.from_dict(metadata_dict)
    assert reconstructed.source == "test_source"
    assert reconstructed.title == "Test Document"


def test_content_creation():
    text = "This is test content"
    metadata = {"source": "test", "language": "en"}

    content = Content(text=text, metadata=metadata)

    assert content.text == text
    assert content.metadata.source == "test"
    assert content.metadata.language == "en"
    assert isinstance(content.id, ContentId)
