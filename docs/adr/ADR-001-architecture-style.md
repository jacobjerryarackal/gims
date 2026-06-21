# ADR-001: Architecture Style — Modular Monolith

**Status:** Accepted | **Date:** 2026-06-21

---

## Context

We have 4 hours to build a production-quality memory system. We need something that:
- Can be deployed quickly to cloud services
- Is easy to test and debug during the hackathon
- Can grow into a larger system later
- Handles failures gracefully

The AI PR Review Agent project uses a "modular monolith" pattern — one main application divided into clear, independent modules. This gives us the best of both worlds: the simplicity of a single application with the organization of a distributed system.

## Decision

We will build a **Modular Monolith** with these components:

### One Backend Application (FastAPI)
A single web service that handles all backend logic. Inside it, we have separate modules for:
- Extracting memories from conversations
- Evaluating whether memories are worth keeping
- Storing and retrieving memories
- Explaining why memories were used
- Managing user permissions and data

### One Frontend Application (Next.js)
A web interface with these pages:
- A chat interface where you talk to the assistant
- A memory dashboard where you see and manage your memories
- An audit log where you see what the system has done

### Two Data Stores
- **PostgreSQL:** Stores all structured information — users, conversations, memory text, scores, audit logs
- **ChromaDB:** Stores mathematical representations of memories that enable "meaning-based" search

### Workflow Orchestration (LangGraph)
Manages the 6-step memory pipeline, ensuring each step completes before the next begins, and handling failures at each step.

## Why This Architecture?

### Advantages
- **Fast to build:** One application to deploy, one codebase to understand
- **Clear boundaries:** Each module has a single, well-defined job
- **Easy to test:** We can test the whole system as one unit
- **Observable:** One place to attach monitoring and logging
- **Future-proof:** If we need to scale later, we can extract modules into separate services

### Trade-offs
- **Single point of failure:** If the main application crashes, everything stops (mitigated by automatic restart)
- **Can't scale parts independently:** We can't add more memory retrieval servers without adding everything else (acceptable for a demo)
- **Orchestration complexity:** Managing the workflow adds some overhead (justified by the resilience it provides)

## Alternatives We Considered

| Approach | Why We Didn't Choose It |
|----------|------------------------|
| Microservices (many small apps) | Too much setup and coordination for 4 hours |
| Serverless functions | Cold starts are too slow for real-time chat |
| Pure AI context window | No persistence — everything is lost when the chat ends |

## Related Documents
- ADR-002: Why we chose PostgreSQL + ChromaDB
- ADR-003: How the memory pipeline works
- ADR-004: How we handle failures

---

*Follows Agentic SWE Kit: modular-architecture and production-readiness principles.*
