"""
Tests for the RAG pipeline's non-LLM components (vector store + document
formatting). The LLM generation step (llm_client.py) requires a live
GROQ_API_KEY and network access, so it's excluded from automated tests here -
verify that manually with: python rag/pipeline.py
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rag"))

from pipeline import row_to_document


def test_row_to_document_format():
    row = pd.Series({
        "record_id": 1001,
        "raw_name": "USA",
        "canonical_name": "United States of America",
        "iso3": "USA",
        "match_method": "alias_override",
        "value": 4500,
    })
    doc = row_to_document(row)
    assert "1001" in doc
    assert "USA" in doc
    assert "United States of America" in doc
    assert "alias_override" in doc