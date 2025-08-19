# RAG and Vector Search Glossary

- Retrieval-Augmented Generation (RAG): A pattern where an LLM retrieves
  relevant context from a knowledge base before generating an answer.
- Embedding: Numeric vector representation of text used for semantic similarity.
- Vector DB: A database that stores and searches embeddings efficiently.
- Cosine similarity: A distance metric measuring angle between vectors; used by
  HNSW index in Chroma when configured with `hnsw:space: cosine`.
- Chunking: Splitting long documents into smaller segments for better retrieval.
- Metadata: Key-value attributes stored with documents, e.g., `type`, `path`,
  `ingested_at` that help filtering or debugging.
- Upsert: Insert or update an existing document in the vector store.
