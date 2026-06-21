# System Architecture Diagram

## High-Level Architecture

This diagram shows how all the pieces of the GPT Intelligence Memory System fit together.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                                                                      │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐   │
│   │   Chat Page  │   │ Memory Mgr   │   │   Audit Dashboard   │   │
│   │   (Next.js)  │   │  (Next.js)   │   │    (Next.js)        │   │
│   └──────┬───────┘   └──────┬───────┘   └──────────┬───────────┘   │
│          │                  │                      │                 │
│          └──────────────────┼──────────────────────┘                 │
│                             │                                        │
│                    HTTPS (secure)                                    │
│                             │                                        │
└─────────────────────────────┼────────────────────────────────────────┘
                              │
┌─────────────────────────────┼────────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                             │
│                                                                      │
│   ┌─────────────────────────┼────────────────────────────────────┐   │
│   │   Authentication │ Rate Limiting │ Logging │ Error Handling  │   │
│   └─────────────────────────┼────────────────────────────────────┘   │
│                             │                                        │
│   ┌─────────────────────────┼────────────────────────────────────┐   │
│   │              MEMORY PIPELINE (LangGraph)                      │   │
│   │                                                                │   │
│   │   ┌──────────┐     ┌──────────┐     ┌──────────┐             │   │
│   │   │ Capture  │────→│ Evaluate │────→│  Store   │             │   │
│   │   │(Extract)│     │ (Gate)   │     │(Persist) │             │   │
│   │   └──────────┘     └────┬─────┘     └────┬─────┘             │   │
│   │                         │                │                    │   │
│   │                    ┌────┴────┐      ┌────┴────┐               │   │
│   │                    │  HITL   │      │  Dedup  │               │   │
│   │                    │ (Queue) │      │ (Merge) │               │   │
│   │                    └─────────┘      └─────────┘               │   │
│   │                                                                │   │
│   │   ┌──────────┐     ┌──────────────┐     ┌──────────┐        │   │
│   │   │ Retrieve │────→│Context Builder│────→│   LLM   │        │   │
│   │   │(Hybrid)  │     │  (Format)    │     │(Generate)│        │   │
│   │   └──────────┘     └──────────────┘     └──────────┘        │   │
│   │                                                                │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                             │                                        │
│   ┌─────────────────────────┼────────────────────────────────────┐   │
│   │              BUSINESS SERVICES                                  │   │
│   │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐     │   │
│   │   │ Memory   │ │ Retrieval│ │  Dedup   │ │ Governance   │     │   │
│   │   │ Service  │ │ Service  │ │ Service  │ │  Service    │     │   │
│   │   └──────────┘ └──────────┘ └──────────┘ └──────────────┘     │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                             │                                        │
└─────────────────────────────┼────────────────────────────────────────┘
                              │
┌─────────────────────────────┼────────────────────────────────────────┐
│                        DATA LAYER                                     │
│                                                                      │
│   ┌─────────────────────────┼────────────────────────────────────┐   │
│   │       PostgreSQL        │          ChromaDB                 │   │
│   │   ┌─────────────────┐   │   ┌─────────────────────────┐     │   │
│   │   │ users           │   │   │ memory_embeddings     │     │   │
│   │   │ conversations   │   │   │ (semantic search)       │     │   │
│   │   │ memories        │◄──┼──→│ metadata              │     │   │
│   │   │ audit_logs      │   │   └─────────────────────────┘     │   │
│   │   │ hitl_queue      │   │                                     │   │
│   │   │ metrics         │   │                                     │   │
│   │   └─────────────────┘   │                                     │   │
│   └─────────────────────────┴────────────────────────────────────┘   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

| Component | Technology | What It Does |
|-----------|-----------|--------------|
| **Chat Page** | Next.js 14 | Where users type messages and see responses |
| **Memory Manager** | Next.js 14 | Where users view, edit, and delete their memories |
| **Audit Dashboard** | Next.js 14 | Where developers see logs and system metrics |
| **API Gateway** | FastAPI | Routes requests, verifies identity, limits abuse, logs activity |
| **Capture Node** | LangGraph + OpenAI | Reads conversations and finds facts worth remembering |
| **Evaluate Node** | LangGraph + OpenAI | Scores memories and decides whether to store them |
| **Store Node** | LangGraph | Saves approved memories to both databases |
| **HITL Queue** | PostgreSQL | Holds uncertain memories for human review |
| **Dedup Service** | Python + ChromaDB | Detects and merges duplicate memories |
| **Retrieve Node** | LangGraph | Searches for relevant memories to answer questions |
| **Context Builder** | LangGraph | Formats memories into a clear summary for the AI |
| **LLM Node** | OpenAI GPT-4o | Generates the final response using memory context |
| **PostgreSQL** | Railway managed | Stores structured data, relationships, audit logs |
| **ChromaDB** | Docker / Railway | Stores mathematical embeddings for meaning-based search |

---

## Data Flow: When a User Sends a Message

| Step | What Happens | Where |
|------|-------------|-------|
| 1 | User types a message in the chat page | Frontend (Vercel) |
| 2 | Message is sent securely to the backend | HTTPS to API Gateway |
| 3 | API Gateway verifies the user's identity | FastAPI middleware |
| 4 | The memory pipeline starts at the Capture node | LangGraph |
| 5 | The Extractor identifies candidate memories | OpenAI API |
| 6 | The Evaluator scores each candidate | OpenAI API |
| 7 | Conditional branch based on score | LangGraph router |
| 8 | High-score memories go to the Store node | LangGraph |
| 9 | Store node saves to PostgreSQL and ChromaDB | Both databases |
| 10 | The Retrieve node searches for relevant memories | Hybrid search |
| 11 | The Context Builder formats memories for the AI | LangGraph |
| 12 | The LLM generates a response using the context | OpenAI API |
| 13 | Response is sent back to the frontend | HTTPS |
| 14 | Frontend displays the response and retrieved memories | Next.js |

---

## Failure Mode Integration

| Failure Mode | Which Component Handles It | Where in the Pipeline |
|--------------|---------------------------|----------------------|
| Memory Pollution | Evaluator (quality gate) | After Capture, before Store |
| Duplicate Memories | Dedup Service | During Store |
| Wrong Retrieval | Retrieval Service | During Retrieve |
| Outdated Memories | Governance Service | During Store and ongoing |
| Vector Search Failure | Circuit Breaker + Fallback | During Retrieve |

---

## Deployment Topology

```
        ┌─────────────┐
        │   Vercel    │  ← Frontend (Next.js)
        │  (Next.js)  │     Serves the web interface
        └──────┬──────┘
               │ HTTPS
               │
               ▼
        ┌─────────────────┐
        │  Railway        │  ← Backend (FastAPI)
        │  (FastAPI)      │     Handles API requests
        │  + PostgreSQL   │     Stores structured data
        │  + Redis        │     Manages job queues
        └────────┬────────┘
                 │
                 │ TCP
                 │
                 ▼
        ┌─────────────────┐
        │  Railway        │  ← Vector Database (ChromaDB)
        │  (Docker)       │     Stores embeddings
        │  (ChromaDB)     │     Enables semantic search
        └─────────────────┘
```

All communication between components is encrypted. The frontend never talks directly to the databases — all data flows through the backend API.

---

*Follows Agentic SWE Kit: modular-architecture, distributed-systems, and production-readiness principles.*
