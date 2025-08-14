# Product FAQ

## What model does the planner use by default for embeddings?
The planner uses sentence-transformers `all-MiniLM-L6-v2` for embeddings when
long-term memory is enabled.

## Where are vectors stored?
Vectors are stored in a Chroma persistent directory at `planner/memory_index`,
managed by `chromadb.PersistentClient`.

## How can I add new knowledge?
Drop `.md` or `.txt` files into `planner/rag`. They are auto-ingested on server
startup into the `planner_memories` collection with metadata type `knowledge`.

## How do I perform a semantic search manually?
Call the endpoint: `/memory/longterm/search?q=your+query&k=5`.

## What about rate limits and retries?
The chat pipeline depends on the configured LLM provider; implement retries and
backoff in the LLM client if needed. The current setup uses Anthropic via
`AnthropicAugmentedLLM` in the MCP agent.
