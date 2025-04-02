# 🧩 rag-ingestor

**`rag-ingestor`** is a microservice responsible for document ingestion and chunking in a Retrieval-Augmented Generation (RAG) chatbot system. It exposes a FastAPI-based REST API that allows uploading and processing documents for downstream embedding and retrieval.

---

## 🚀 Features

- 📄 Load plain text documents
- ✂️ Chunk text for embedding
- ⚡ Exposes a FastAPI API
- 🐳 Dockerized & K8s-ready
- 📦 Managed with Poetry
- 🧪 Fully testable with `pytest`, `ruff`, and `black`

---

## 📁 Project Structure

```
.
├── src/
│   └── rag_ingestor/       # Python package
│       ├── main.py         # FastAPI app entrypoint
│       └── ingestion/      # Document loading + chunking
├── tests/                  # Unit tests
├── Dockerfile              # Container build definition
├── Makefile                # Dev utilities
├── pyproject.toml          # Poetry config
└── .pre-commit-config.yaml # Format & lint hooks
```

---

## 🛠️ Installation

### Local Dev

```bash
poetry install
poetry run uvicorn rag_ingestor.main:app --reload
```

API is served at: [http://localhost:8001](http://localhost:8001)

---

## 🐳 Docker

### Build

```bash
docker build -t rag-ingestor:dev .
```

### Run

```bash
docker run -p 8001:8001 rag-ingestor:dev
```

---

## 🧪 Testing & Linting

### Run all checks

```bash
make check
```

### Run tests only

```bash
make test
```

### Format code

```bash
make format
```

---

## ⚙️ CI/CD

This repo uses GitHub Actions for:

- ✅ Code formatting (`black`)
- ✅ Linting (`ruff`)
- ✅ Unit tests (`pytest`)

All workflows are defined in `.github/workflows`.



