# ADR-002: Database & Vector Store Strategy — PostgreSQL + ChromaDB

**Status:** Accepted | **Date:** 2026-06-21

---

## Context

Our memory system needs two different kinds of data storage:

1. **Structured storage** for things like user profiles, conversation records, memory metadata, audit logs, and governance data. This needs to support complex queries, relationships, and strict consistency.

2. **Vector storage** for semantic search. When a user asks "What should I learn next?" we need to find memories that are conceptually related — even if they don't use the exact same words. This requires storing mathematical representations (embeddings) of text and searching by similarity.

The AI PR Review Agent uses a single managed database (Tiger Cloud) that handles both structured and vector data. For our 4-hour hackathon, we need tools that are simpler to set up but follow the same design principles.

## Decision

We will use **PostgreSQL + ChromaDB** as our data layer:

### PostgreSQL (via Railway)
Handles all structured data:
- User accounts and preferences
- Conversation history
- Memory records with metadata (type, scores, dates, status)
- Audit logs for compliance
- Human review queues
- System health metrics

### ChromaDB (in-process or Docker)
Handles vector data:
- Stores mathematical embeddings of memory text
- Enables "find similar meaning" searches
- Supports filtering by metadata (e.g., only search active memories of a specific type)

## How Data Flows Through the System

```
Conversation Message
        |
        v
Memory Extractor (identifies facts)
        |
        v
Memory Evaluator (scores quality)
        |
        v
PostgreSQL (stores text, scores, metadata)
        |
        v
ChromaDB (stores mathematical representation)
        |
        v
Retrieval Service (searches both databases)
        |
        v
Context Builder (formats results)
        |
        v
AI Response (uses memories to answer)
```

## Design Principles

1. **PostgreSQL is the source of truth:** All structured data lives here. If ChromaDB ever has a problem, we can rebuild it from PostgreSQL.

2. **Every operation is safe to retry:** If a network error happens during storage, doing the same operation again won't create duplicates.

3. **Everything is logged:** Every memory creation, update, retrieval, and deletion is recorded in the audit log.

4. **Soft deletes:** Memories are never permanently deleted. They are marked as inactive, preserving the audit trail.

## Why This Combination?

### Advantages
- **Familiar tools:** PostgreSQL and ChromaDB are well-documented and easy to deploy
- **Fast setup:** No managed service signup required
- **Clear separation:** Structured data and vector data have distinct responsibilities
- **Robust search:** Combining both gives us the best of keyword matching and meaning-based search

### Trade-offs
- **Two databases to manage:** We need to keep connections to both systems
- **Consistency risk:** Data could theoretically drift between the two (mitigated by storing ChromaDB references in PostgreSQL)
- **Audit logs will grow:** We may need to archive old logs eventually (not a concern for the demo)

## Alternatives We Considered

| Alternative | Why We Didn't Choose It |
|-------------|------------------------|
| Tiger Cloud (TimescaleDB + pgvectorscale) | Requires managed service signup and learning curve; too much for 4 hours |
| SQLite + ChromaDB | SQLite isn't robust enough for concurrent access in production |
| MongoDB + Pinecone | Adds unnecessary complexity; Pinecone is an external dependency |
| Pure ChromaDB | Can't do structured queries or audit trails |

## Related Documents
- ADR-001: Overall architecture style
- ADR-003: How the pipeline orchestrates data flow
- `/docs/schemas/database-schema.sql` — Full database design

---

*Follows Agentic SWE Kit: data-systems-engineering and production-readiness principles.*
