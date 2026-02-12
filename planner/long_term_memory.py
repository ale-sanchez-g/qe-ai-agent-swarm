from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import threading

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
except Exception as e:
    chromadb = None
    SentenceTransformer = None
    _IMPORT_ERROR = e
else:
    _IMPORT_ERROR = None


class LongTermMemory:
    """
    Persistent vector memory for long-term recall and RAG.

    - Embeds text with sentence-transformers
    - Stores vectors in Chroma persistent DB
    - Thread-safe basic upsert and search
    """

    def __init__(
        self,
        persist_dir: Path | str,
        collection_name: str = "planner_memories",
        model_name: str = "all-MiniLM-L6-v2",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        if chromadb is None or SentenceTransformer is None:
            raise RuntimeError(
                f"LongTermMemory dependencies missing: {str(_IMPORT_ERROR)}"
            )

        self.persist_dir = str(persist_dir)
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        # Initialize embedding model
        self.embedder = SentenceTransformer(model_name)

        # Initialize Chroma persistent client/collection
        self.client = chromadb.PersistentClient(
            path=self.persist_dir, settings=Settings(allow_reset=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata=metadata or {"hnsw:space": "cosine"}
        )

        self._lock = threading.Lock()

    def embed(self, texts: List[str]) -> List[List[float]]:
        return self.embedder.encode(texts, normalize_embeddings=True).tolist()

    def upsert(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        if not texts:
            return
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        if metadatas is None:
            metadatas = [{} for _ in texts]

        vectors = self.embed(texts)
        with self._lock:
            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=vectors,
                metadatas=metadatas,
            )

    def search(
        self,
        query: str,
        k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not query:
            return []
        query_vec = self.embed([query])[0]
        with self._lock:
            res = self.collection.query(
                query_embeddings=[query_vec],
                n_results=k,
                where=where,
                where_document=where_document,
            )
        # Normalize into a list of {text, metadata, id, distance}
        out = []
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for i in range(len(ids)):
            out.append(
                {
                    "id": ids[i],
                    "text": docs[i],
                    "metadata": metas[i],
                    "distance": dists[i],
                }
            )
        return out

    def ingest_folder(
        self,
        folder: Path | str,
        glob_pattern: str = "**/*.txt",
        doc_type: str = "report",
        max_bytes: int = 200_000,
    ) -> int:
        """
        Index all text files in a folder as long-term memory documents.
        Returns the count of files ingested.
        """
        folder = Path(folder)
        if not folder.exists():
            return 0

        texts, metadatas, ids = [], [], []
        for fp in folder.glob(glob_pattern):
            try:
                content = fp.read_text(encoding="utf-8")
                if len(content.encode("utf-8")) > max_bytes:
                    # Truncate very large files to keep token limits reasonable
                    content = content[:max_bytes]
                texts.append(content)
                metadatas.append(
                    {
                        "type": doc_type,
                        "path": str(fp),
                        "filename": fp.name,
                        "ingested_at": int(time.time()),
                    }
                )
                ids.append(f"file::{str(fp)}")
            except Exception:
                continue

        if texts:
            self.upsert(texts=texts, metadatas=metadatas, ids=ids)
        return len(texts)
