# Incident Postmortem — 2024-11-15

Severity: SEV-2
Impact: Elevated 5xx errors for 37 minutes on the Planner Chat API

## Summary
At 09:12 UTC, deployments introduced an incompatible change to the embedding
model cache. New requests failed to compute embeddings, causing RAG retrieval to
return empty context. The API still responded but with degraded answers.

## Timeline
- 09:12 — Deployment rolled out to 100%
- 09:14 — Error rate crosses alert threshold
- 09:18 — Mitigation started: rollback initiated
- 09:28 — Rollback complete
- 09:49 — Cache invalidation executed and verified

## Root Cause
A mismatch between the serialized embedding model version and the running
`sentence-transformers` code path caused cache deserialization failures.

## Corrective Actions
- Add startup check to verify embedding model and cache compatibility
- Automate cache invalidation on model version change
- Expand canary duration for memory subsystem changes

## Lessons Learned
- RAG components must be validated in staging with cache warmup
- Canarying storage layers needs explicit functional checks, not just health
