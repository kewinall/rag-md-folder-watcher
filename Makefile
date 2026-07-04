.PHONY: test build up up-rocky down logs clean

test:
	python -m pytest -q

build:
	docker compose build

up:
	docker compose up -d --build

up-rocky:
	docker compose -f compose.yaml -f compose.rocky.yaml up -d --build

down:
	docker compose down

logs:
	docker compose logs -f rag-md-watcher

clean:
	rm -rf .pytest_cache __pycache__ app/__pycache__ rag_md_converter/__pycache__ data
