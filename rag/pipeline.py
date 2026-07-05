"""
End-to-end RAG pipeline: load standardized dataset -> embed into vector
store -> retrieve relevant records for a query -> generate an LLM answer
grounded in those records.

This is what turns the cleaned ETL output into an "LLM-ready" / semantic
search / RAG-experimentation asset, rather than just a clean CSV.
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etl"))

from vector_store import VectorStore
from llm_client import generate_answer


def row_to_document(row: pd.Series) -> str:
    """Turn a standardized-country row into a natural language sentence for embedding."""
    return (
        f"Record {row['record_id']}: raw name '{row['raw_name']}' was standardized to "
        f"'{row['canonical_name']}' (ISO3: {row['iso3']}) via {row['match_method']}, "
        f"with an associated value of {row['value']}."
    )


def build_vector_store_from_csv(csv_path: str, collection_name: str = "country_records") -> VectorStore:
    df = pd.read_csv(csv_path)
    store = VectorStore(collection_name=collection_name)

    documents = df.apply(row_to_document, axis=1).tolist()
    ids = [str(rid) for rid in df["record_id"]]
    metadatas = df[["canonical_name", "iso3", "match_method"]].fillna("").to_dict("records")

    store.add_records(documents=documents, ids=ids, metadatas=metadatas)
    return store


def ask(store: VectorStore, question: str, n_results: int = 3) -> dict:
    """
    Full RAG round-trip: retrieve relevant chunks, then generate an answer.
    Returns both the retrieved context and the generated answer for
    transparency/debugging (important in an interview - show your retrieval,
    don't just show the final text).
    """
    results = store.query(question, n_results=n_results)
    retrieved_chunks = results["documents"][0] if results["documents"] else []

    answer = generate_answer(question, retrieved_chunks)

    return {
        "question": question,
        "retrieved_chunks": retrieved_chunks,
        "answer": answer,
    }


if __name__ == "__main__":
    store = build_vector_store_from_csv("../data/processed/standardized_countries.csv")
    print(f"Indexed {store.count()} records.")

    result = ask(store, "What ISO code was assigned to records about the United States?")
    print("\nRetrieved context:")
    for chunk in result["retrieved_chunks"]:
        print(f"  - {chunk}")
    print(f"\nAnswer: {result['answer']}")