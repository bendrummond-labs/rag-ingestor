.PHONY: format lint check test docker-build docker-run docker-push docker-clean

format:
	poetry run black src tests

lint:
	poetry run ruff check src tests

check: format lint

test:
	poetry run pytest tests

docker-build:
	docker build -t rag-ingestor:latest .

docker-run:
	docker run -p 8001:8001 rag-ingestor:latest


docker-push:
	docker tag rag-ingestor:latest ghcr.io/bendrummond-labs/rag-ingestor:latest
	docker push ghcr.io/bendrummond-labs/rag-ingestor:latest

docker-clean:
	docker rmi rag-ingestor:latest || true
	docker rmi ghcr.io/bendrummond-labs/rag-ingestor:latest || true

docker-all: docker-clean docker-build docker-run