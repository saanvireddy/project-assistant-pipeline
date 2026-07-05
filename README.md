# Project Assistant Pipeline

An end-to-end AI-ready data engineering pipeline built during my Project Assistant role at the University of South Florida (Feb 2025 – May 2026). It standardizes messy real-world country data, enriches it with U.S. Census demographic/income data, and makes the results queryable through a Retrieval-Augmented Generation (RAG) pipeline — all automated, tested, and run through CI/CD.

[![CI](https://github.com/saanvireddy/project-assistant-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/saanvireddy/project-assistant-pipeline/actions/workflows/ci.yml)

## What this does

Real-world datasets rarely come clean — country names show up as "USA," "U.S.A.," "United States of America," or historical entities like "USSR" that no longer exist. This pipeline:

1. **Standardizes** messy country name variants into official ISO 3166-1 codes using fuzzy matching
2. **Validates** the results against a defined schema and runs automated data quality checks
3. **Engineers features** (income ratios, population buckets, confidence tiers) for downstream analytics
4. **Enriches** the data with real U.S. Census Bureau demographic/income data at state, county, and ZIP granularity
5. **Indexes** the results into a vector store and exposes them through an LLM-powered semantic search / RAG pipeline
6. **Automates** the entire run end-to-end, with test coverage and CI/CD on every push

## Architecture
project-assistant-pipeline/

├── etl/                 # Country name → ISO code standardization (RapidFuzz)

│   ├── country_standardizer.py

│   ├── country_overrides.py

│   └── iso_reference.py

├── modules/              # Reusable schema validation, quality checks, feature engineering

│   ├── schema_validator.py

│   ├── quality_checks.py

│   ├── feature_engineering.py

│   └── exceptions.py

├── census/               # U.S. Census ACS 5-Year API integration (FIPS-based)

│   ├── acs_client.py

│   ├── fips_lookup.py

│   └── pipeline.py

├── rag/                  # Vector store + LLM retrieval (semantic search / RAG)

│   ├── vector_store.py

│   ├── llm_client.py

│   └── pipeline.py

├── pipeline/              # End-to-end orchestration

│   └── orchestrator.py

├── tests/                # 42 unit tests across all modules

├── data/

│   ├── raw/               # Input data (sample records + real ISO reference dataset)

│   └── processed/          # Pipeline outputs

└── .github/workflows/       # CI/CD (GitHub Actions)

## Key design decisions

- **Real reference data, not invented data.** The ISO country list comes from a public, MIT-licensed dataset ([lukes/ISO-3166-Countries-with-Regional-Codes](https://github.com/lukes/ISO-3166-Countries-with-Regional-Codes)) — 249 real countries/territories with official ISO codes. Only the sample "messy input" records are synthetic test data.
- **Overrides before fuzzy matching.** Abbreviations (USA, UK, UAE) and historical entities (USSR, West/East Germany → present-day successor states) are resolved through explicit, auditable override dictionaries before falling back to fuzzy matching — this keeps ambiguous historical assumptions visible rather than silently guessed.
- **Non-country entities aren't force-matched.** Supranational references like "EU" are deliberately flagged as non-standardizable rather than mapped to an incorrect single country.
- **ZCTA queries hit a real Census API limitation.** ZIP Code Tabulation Areas can span state lines, so the Census API rejects state-scoped ZCTA queries. This pipeline pulls ZCTA data nationally and filters by ZIP prefix range instead — a documented workaround, not a guess.
- **Every pipeline stage fails independently.** The orchestrator records success/failure per stage in a run manifest rather than letting one failure (e.g., a third-party API being briefly unreachable) silently corrupt the whole run.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root (never committed — already in `.gitignore`):
GROQ_API_KEY=your_groq_key

CENSUS_API_KEY=your_census_key

- Groq key: [console.groq.com](https://console.groq.com) → API Keys
- Census key: [api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html)

## Running it

**Run the full automated pipeline:**
```bash
cd pipeline
python orchestrator.py
```
This runs ingestion → standardization → feature engineering → validation/quality checks → RAG indexing, and writes a `pipeline_manifest.json` with per-stage status and timing.

**Run individual pieces:**
```bash
cd etl && python country_standardizer.py       # ETL only
cd census && python pipeline.py                # Census API pull (Florida example)
cd rag && python pipeline.py                   # RAG query demo
```

**Run the test suite:**
```bash
python -m pytest tests/ -v
```
42 tests covering ETL matching logic, schema validation, quality checks, feature engineering, Census API request-building (mocked, no live calls needed), and orchestrator stage tracking.

## Results

- **96.1% match rate** standardizing messy country name variants against the full 249-country ISO reference list
- **Zero unmatched records** after iterative override refinement (only 2 deliberately flagged as non-standardizable: EU, European Union)
- **CI passes on every push** — full test suite + ETL smoke test run automatically via GitHub Actions

## Tech stack

Python · pandas · RapidFuzz · ChromaDB · Groq (Llama 3.3 70B) · U.S. Census Bureau ACS API · pytest · GitHub Actions
