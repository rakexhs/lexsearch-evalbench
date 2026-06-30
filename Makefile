# Lexsearch EvalBench — Makefile
# venv-based local workflow. `make setup` then `make demo` reproduces everything.

PY := python3
VENV := .venv
BIN := $(VENV)/bin
PYTHON := $(BIN)/python
PIP := $(BIN)/pip

.DEFAULT_GOAL := help
.PHONY: help setup sample-data index eval ablate run-api run-ui test bench clean demo

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## Create .venv and install dependencies
	$(PY) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ setup complete. Activate with: source $(VENV)/bin/activate"

sample-data: ## (Re)generate the built-in sample corpus + golden questions
	$(PYTHON) scripts/setup_sample_data.py

index: ## Ingest corpus, chunk, and build BM25 + dense indexes
	$(PYTHON) scripts/build_indexes.py

eval: ## Run the retrieval/answer evaluation across all methods
	$(PYTHON) scripts/run_eval.py

ablate: ## Run ablation experiments (chunk size, overlap, hybrid weight, rerank)
	$(PYTHON) scripts/run_ablations.py

bench: ## Benchmark per-query latency by method
	$(PYTHON) scripts/benchmark_latency.py

run-api: ## Start the FastAPI backend on :8000
	$(BIN)/uvicorn app.main:app --reload --port 8000

run-ui: ## Start the Streamlit dashboard on :8501
	$(BIN)/streamlit run ui/streamlit_app.py

test: ## Run the test suite
	$(BIN)/pytest -q

demo: sample-data index eval ## End-to-end: data -> index -> eval
	@echo "✅ demo pipeline complete. See reports/results.md"

clean: ## Remove venv, caches, db, indexes, and generated artifacts
	rm -rf $(VENV) .pytest_cache **/__pycache__ app/**/__pycache__
	rm -rf data/index data/lexsearch.db
	rm -f reports/*.csv reports/*.json reports/charts/*.png
	@echo "🧹 cleaned."
