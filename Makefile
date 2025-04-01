.PHONY: format lint check

format:
	poetry run black src tests

lint:
	poetry run ruff check src tests

check: format lint
