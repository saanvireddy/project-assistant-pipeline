"""
Vector store wrapper around ChromaDB for semantic search over pipeline
datasets (e.g. standardized country/demographic records).

Uses ChromaDB's default embedding function (all-MiniLM-L6-v2, downloaded
automatically on first use) unless a custom embedding_function is passed in.
"""

import chromadb


class VectorStore:
    def __init__(self, collection_name: str = "pipeline_data", persist_directory: str = None, embedding_function=None):
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.Client()

        kwargs = {"name": collection_name}
        if embedding_function is not None:
            kwargs["embedding_function"] = embedding_function

        self.collection = self.client.get_or_create_collection(**kwargs)

    def add_records(self, documents: list, ids: list, metadatas: list = None) -> None:
        """
        Add documents to the vector store.
        documents: list of text strings to embed (e.g. "Country: Germany, Value: 2900")
        ids: unique string ID per document
        metadatas: optional list of dicts with structured fields for filtering
        """
        self.collection.add(documents=documents, ids=ids, metadatas=metadatas)

    def query(self, query_text: str, n_results: int = 3, where: dict = None) -> dict:
        """
        Retrieve the n_results most semantically similar documents to query_text.
        where: optional metadata filter, e.g. {"match_method": "alias_override"}
        """
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
        )

    def count(self) -> int:
        return self.collection.count()