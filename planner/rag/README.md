# Planner RAG Test Corpus

This folder contains a small, diverse knowledge base to validate the RAG pipeline.
Documents cover different domains and formats (markdown/text) so you can verify
chunking, embedding, indexing, and retrieval quality.

## Files
- glossary.md — Common RAG and vector search terminology
- product_faq.md — FAQ-style Q&A to test precise retrieval
- incidents/postmortem-2024-11-15.md — Narrative incident report with timeline
- howtos/setup_chroma.txt — Step-by-step guide with commands
- architecture/overview.md — System context and components

## Suggested test queries
Try these in the chat UI or the `/memory/longterm/search?q=...` endpoint:
- "What is vector similarity search and how does it work here?"
- "How do I set up the Chroma persistent client?"
- "Summarize the incident on 2024-11-15 and list root cause and actions."
- "What are recommended chunk sizes for RAG?"
- "Where does the planner store its memory index?"
- "Give me FAQs about rate limits and retries."

## Verify retrieval
- The top results should show metadata type `knowledge` and relevant filenames.
- Distances should be lower for more relevant hits (cosine space).
- In responses, retrieved snippets appear under "Retrieved Knowledge:".

## Notes
- You can add more files here; they will be auto-ingested on startup.
- Very large files are truncated to 200kB per `ingest_folder`.
