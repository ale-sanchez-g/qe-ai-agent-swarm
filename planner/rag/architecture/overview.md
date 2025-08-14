# Planner Architecture Overview

The Planner Chat UI uses FastAPI with WebSocket support. Conversation memory is
managed by LangChain's ConversationSummaryBufferMemory and persisted to SQLite
per session. Long-term memory is powered by Chroma for vector storage and
sentence-transformers for embeddings.

Key components:
- `plannerChat.py`: FastAPI app, WebSocket handling, RAG orchestration
- `memory_manager.py`: Conversation memory and session management
- `long_term_memory.py`: Chroma-backed vector store wrapper
- `memory_index/`: Persistent directory for Chroma's sqlite and HNSW index
- `output/`: Saved conversations and reports, optionally ingested

RAG flow:
1. User asks a question.
2. Conversation context is built from recent history + summary.
3. Semantic search runs against long-term memory (Chroma) with `k=5`.
4. Retrieved snippets are concatenated and provided to the LLM.
5. Response is generated and stored; the Q/A pair is also upserted into memory.
