# Project Assistant Pipeline

AI-ready data engineering pipeline built as a USF Project Assistant, covering:

- Country name → ISO code standardization (fuzzy matching)
- Reusable data cleaning / validation / QA modules
- U.S. Census ACS 5-Year API integration (FIPS-based)
- RAG pipeline (vector store + LLM) over processed datasets
- CI/CD via GitHub Actions

## Structure
- `etl/` — country name standardization
- `modules/` — reusable cleaning, validation, QA components
- `census/` — ACS API integration
- `rag/` — semantic search + LLM retrieval
- `pipeline/` — end-to-end orchestration
- `tests/` — unit tests

## Setup
```bash
pip install -r requirements.txt
```

## Status
🚧 In progress — built incrementally, one module at a time.
