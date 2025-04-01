FROM python:3.11-slim

# Install Poetry
RUN pip install --no-cache-dir poetry

# Set workdir
WORKDIR /src

# Copy poetry files
COPY pyproject.toml poetry.lock* README.md ./


COPY src/ ./src

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Run the FastAPI app
CMD ["uvicorn", "rag_ingestor.main:app", "--host", "0.0.0.0", "--port", "8001"]
