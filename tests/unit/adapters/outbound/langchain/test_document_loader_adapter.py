import pytest
from pathlib import Path
import tempfile
from rag_ingestor.adapters.outbound.langchain.document_loader_adapter import (
    LangchainDocumentLoaderAdapter,
)


@pytest.fixture
def text_file():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"This is a test document.\nIt has multiple lines.\n")
        path = Path(f.name)
    yield path
    path.unlink()


def test_load_text_document(text_file):
    adapter = LangchainDocumentLoaderAdapter()

    contents = adapter.load_content(text_file)

    assert len(contents) == 1
    assert "This is a test document" in contents[0].text
    assert contents[0].metadata.source == str(text_file)


def test_unsupported_extension():
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        path = Path(f.name)

    try:
        adapter = LangchainDocumentLoaderAdapter()

        with pytest.raises(ValueError, match="Unsupported file type"):
            adapter.load_content(path)
    finally:
        path.unlink()
