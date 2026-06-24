# Repository Structure

This document describes how the project files are organized. The structure follows the principle of **modular architecture** — each part of the system has its own clearly defined space.

---

## Top-Level Layout

```
gims/                           ← Main project folder
│
├── .github/                    ← GitHub automation
│   └── workflows/
│       └── ci.yml              ← Automatic testing on every code change
│
├── docs/                       ← All documentation (this is where you are now)
│   ├── PRD.md                  ← What we're building and why
│   ├── adr/                    ← Architecture decisions and reasoning
│   │   ├── ADR-001-architecture-style.md
│   │   ├── ADR-002-database-strategy.md
│   │   ├── ADR-003-pipeline-orchestration.md
│   │   ├── ADR-004-failure-mode-strategy.md
│   │   └── ADR-005-security-governance.md
│   ├── api/
│   │   └── openapi-spec.yaml   ← Complete API contract
│   ├── architecture/
│   │   ├── repository-structure.md   ← This file
│   │   └── system-diagram.md         ← Visual system architecture
│   ├── deployment/
│   │   └── deployment-guide.md     ← How to deploy to production
│   ├── failure-modes/
│   │   ├── FM-001-memory-pollution.md
│   │   ├── FM-002-duplicate-memories.md
│   │   ├── FM-003-wrong-retrieval.md
│   │   ├── FM-004-outdated-memories.md
│   │   └── FM-005-vector-search-failure.md
│   ├── schemas/
│   │   └── database-schema.sql     ← Complete database design
│   └── backlog/
│       └── implementation-plan.md  ← Hour-by-hour build plan
│
├── backend/                    ← The server application (FastAPI)
│   ├── api/                    ← Web endpoints that the frontend calls
│   │   ├── routes/
│   │   │   ├── chat.py         ← Send a message, get a response
│   │   │   ├── memories.py     ← View, create, edit, delete memories
│   │   │   ├── hitl.py         ← Human review queue management
│   │   │   ├── audit.py        ← View audit logs
│   │   │   └── metrics.py      ← System health metrics
│   │   ├── middleware/
│   │   │   ├── auth.py         ← Verify who you are
│   │   │   ├── rate_limit.py   ← Prevent abuse
│   │   │   └── logging.py      ← Record what happens
│   │   └── dependencies.py     ← Shared resources (database connections, etc.)
│   │
│   ├── agents/                 ← The AI pipeline components
│   │   ├── extractor.py        ← Finds facts worth remembering
│   │   ├── evaluator.py        ← Judges memory quality
│   │   ├── retriever.py        ← Finds relevant memories
│   │   ├── explainability.py   ← Explains why memories were retrieved
│   │   └── pipeline.py         ← Orchestrates the whole flow
│   │
│   ├── core/                     ← Shared foundation
│   │   ├── config.py             ← Settings and environment variables
│   │   ├── exceptions.py         ← Custom error types
│   │   └── security.py           ← Encryption and hashing
│   │
│   ├── models/                   ← Database table definitions
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── memory.py
│   │   ├── audit.py
│   │   └── hitl.py
│   │
│   ├── services/                 ← Business logic
│   │   ├── memory_service.py     ← Create, read, update, delete memories
│   │   ├── retrieval_service.py  ← Search and rank memories
│   │   ├── dedup_service.py      ← Find and merge duplicates
│   │   ├── governance_service.py ← User management and consent
│   │   └── health_service.py     ← Check if everything is working
│   │
│   ├── storage/                  ← Database connections
│   │   ├── postgres.py           ← Connect to PostgreSQL
│   │   └── chroma.py             ← Connect to ChromaDB
│   │
│   ├── utils/                    ← Helper tools
│   │   ├── embeddings.py         ← Convert text to mathematical representations
│   │   ├── circuit_breaker.py    ← Handle service failures gracefully
│   │   ├── retry.py              ← Try again with delays
│   │   └── telemetry.py          ← Track performance and errors
│   │
│   ├── tests/                    ← Automated tests
│   │   ├── test_extractor.py
│   │   ├── test_evaluator.py
│   │   ├── test_retrieval.py
│   │   ├── test_dedup.py
│   │   └── test_api.py
│   │
│   ├── alembic/                  ← Database version control
│   │   ├── versions/             ← Individual migration files
│   │   └── env.py                ← Migration configuration
│   │
│   ├── Dockerfile                ← How to build the backend as a container
│   ├── requirements.txt          ← List of dependencies
│   └── main.py                   ← Application entry point
│
├── frontend/                     ← The web interface (Next.js)
│   ├── app/                      ← Page routes
│   │   ├── layout.tsx            ← Shared page structure
│   │   ├── page.tsx              ← Landing page
│   │   ├── chat/
│   │   │   └── page.tsx          ← Main chat interface
│   │   ├── memories/
│   │   │   └── page.tsx          ← Memory management dashboard
│   │   └── audit/
│   │       └── page.tsx          ← Audit log viewer
│   │
│   ├── components/               ← Reusable UI pieces
│   │   ├── ChatInterface.tsx     ← Message input and display
│   │   ├── MemorySidebar.tsx     ← Shows retrieved memories
│   │   ├── MemoryCard.tsx        ← Single memory display
│   │   ├── MemoryManager.tsx     ← CRUD operations UI
│   │   ├── ExplainabilityPanel.tsx ← Why was this retrieved?
│   │   
│   │
│   ├── lib/                      ← Shared utilities
│   │   ├── api.ts                ← Typed API client
│   │   └── auth.ts               ← Authentication handling
│   │
│   ├── types/                    ← Type definitions
│   │   └── index.ts
│   │
│   ├── public/                   ← Static assets (images, fonts)
│   └── package.json              ← Frontend dependencies
│
├── scripts/                      ← Automation scripts
│   ├── init-db.sh                ← Set up local database
│   ├── seed-data.sql             ← Demo data
│   └── deploy-railway.sh         ← Deploy to production
│
├── docker-compose.yml            ← Start everything locally with one command
├── .env.example                  ← Template for environment variables
├── .gitignore                    ← Files to exclude from version control
├── Makefile                      ← Common commands (start, test, deploy)
└── README.md                     ← Project overview and quick start
```

---

## Key Design Decisions

| Decision | What It Means | Why We Chose It |
|----------|--------------|-----------------|
| **Modular monolith** | One application with clearly separated internal modules | Fast to build, easy to test, can split into separate services later |
| **LangGraph for pipeline** | Workflow engine manages the 6-step memory process | Checkpointing, conditional branching, future extensibility |
| **Separate agents folder** | AI reasoning logic is isolated from business logic | Clear boundary, easy to test independently |
| **Storage abstraction** | Database connections are wrapped in reusable modules | Can swap PostgreSQL/ChromaDB for other tools later |
| **Feature-based frontend routing** | URLs match user mental models (/chat, /memories, /audit) | Intuitive navigation |
| **Makefile for automation** | Single place for common commands | Consistency across team members and CI/CD |

---

## How the Structure Supports Quality

| Quality Attribute | How the Structure Helps |
|-------------------|------------------------|
| **Testability** | Each module can be tested independently; tests are in a dedicated folder |
| **Observability** | Middleware, telemetry, and audit logs are built into the structure |
| **Security** | Auth, rate limiting, and encryption are centralized in dedicated modules |
| **Maintainability** | Clear boundaries mean changes in one area don't ripple unpredictably |
| **Scalability** | Modules can be extracted into separate services when needed |

---

*Follows Agentic SWE Kit: modular-architecture and production-readiness principles.*
