.PHONY: install test ingest

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest

ingest:
	python -m data_gouv_ingestion.cli
