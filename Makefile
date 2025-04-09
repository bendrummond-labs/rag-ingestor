.PHONY: format lint check test clean clean-py clean-all docker-build docker-run docker-push docker-clean docker-all

format:
	poetry run black src tests

lint:
	poetry run ruff check src tests

check: format lint

clean-py:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

clean: clean-py
	rm -rf .coverage htmlcov .pytest_cache

clean-all: clean
	rm -rf .venv

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