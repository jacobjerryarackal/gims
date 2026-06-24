# Implementation Plan: MVP

## Philosophy

We follow the Design Template + Failure Modes framework's guidance on prototype scope:
- **Build the simplest version that proves the concept works**
- **Pick the highest-volume, simplest path first**
- **Measure against a manual baseline, not perfection**
- **One metric that proves value:** Retrieval Accuracy of 85% or higher

---

## Time Allocation

| Hour | Phase | What We Build | Risk Level |
|------|-------|---------------|------------|
| **0:00 – 0:30** | Setup & Infrastructure | Get all tools running locally | Low |
| **0:30 – 1:30** | Backend Core | Database, API framework, basic endpoints | Medium |
| **1:30 – 2:30** | Memory Pipeline | Extract, evaluate, and store memories | High |
| **2:30 – 3:15** | Retrieval & Explainability | Find memories and explain why | High |
| **3:15 – 3:45** | Frontend Shell | Chat interface and memory dashboard | Medium |
| **3:45 – 4:00** | Integration & Demo | Wire everything together, run demo | Medium |

---

## Phase 0: Setup (0:00 – 0:30) — 30 minutes

### Backend Setup (15 minutes)
- Create the backend project folder
- Set up a virtual environment for Python dependencies
- Install required packages: FastAPI (web framework), SQLAlchemy (database), asyncpg (async database driver), ChromaDB (vector database), OpenAI client, LangGraph (workflow engine), and Pydantic (data validation)
- Create a basic web application with a health check endpoint at `/health`
- Create a configuration file for environment variables (API keys, database URLs, etc.)

### Database Setup (10 minutes)
- Start PostgreSQL and ChromaDB using Docker Compose (one command starts both)
- Run the database schema file to create all tables
- Verify tables exist by listing them in the database

### Frontend Setup (5 minutes)
- Create a new Next.js project with TypeScript and Tailwind CSS
- Install UI component libraries for dialogs and icons

### Checkpoint
Open a browser and visit `http://localhost:8000/health` — you should see a "healthy" response.

---

## Phase 1: Backend Core (0:30 – 1:30) — 60 minutes

### Database Models (15 minutes)
Create the data structure definitions for:
- **User:** ID, email, name, account status, consent flag
- **Conversation:** ID, user reference, title, timestamps, memory consent flag
- **Conversation Turn:** ID, conversation reference, who spoke (user/assistant), message content, timestamp
- **Memory:** ID, user reference, conversation reference, type (semantic/procedural/episodic), content, quality scores, status, timestamps, expiration date, access count, last accessed date

Use Python enums for memory types and statuses to prevent invalid values.

Set up relationships: A User has many Conversations. A Conversation has many Turns. A Turn can generate many Memories.

### Storage Layer (20 minutes)
Build two connection modules:
- **PostgreSQL connection:** Async database engine with connection pooling
- **ChromaDB connection:** Client wrapper that manages collections and handles errors

Test by inserting a sample memory and verifying it appears in both databases.

### API Routes (25 minutes)
Build the core web endpoints:
- **POST /api/v1/chat:** Accept a user message, return a response (initially just an echo; AI integration comes later)
- **GET /api/v1/memories:** List all memories for a user, with optional filtering by type or status
- **POST /api/v1/memories:** Manually create a memory (for governance and testing)
- **DELETE /api/v1/memories/{id}:** Soft-delete a memory (marks it inactive, doesn't truly delete)

### Checkpoint
All endpoints return successful responses when tested with sample data.

---

## Phase 2: Memory Pipeline (1:30 – 2:30) — 60 minutes

### Extractor Agent (20 minutes)
Build the component that reads conversations and finds facts worth remembering.

How it works:
- Takes the user's message as input
- Sends it to an AI model with a carefully crafted instruction: "Extract all facts, preferences, and events the user explicitly stated about themselves"
- The AI returns a structured list of candidate memories, each tagged with its type (semantic, procedural, or episodic)
- Includes examples in the instructions to guide the AI (e.g., "I am an AI Engineer" = semantic, "I prefer first-principles" = procedural)

### Evaluator Agent (20 minutes)
Build the quality gate that decides whether a memory is worth storing.

How it works:
- Takes each candidate memory from the extractor
- Scores it on three dimensions: relevance (is this useful?), novelty (is this new?), accuracy (is this true?)
- Checks novelty by searching the existing memory database for similar entries
- Applies the routing rules:
  - Above 0.85 average: Store automatically
  - 0.70 to 0.85: Check for duplicates first
  - 0.50 to 0.70: Queue for human review
  - Below 0.50: Reject and log

### Storage Integration (15 minutes)
Wire the extractor and evaluator together:
- Extractor output flows into the evaluator
- Evaluator output flows into storage (for approved memories) or rejection (for failed ones)
- Generate mathematical embeddings for each approved memory using the OpenAI embedding service
- Store the text and metadata in PostgreSQL
- Store the embedding in ChromaDB with a reference back to the PostgreSQL record

### LangGraph Pipeline (5 minutes)
Define the workflow as a state graph:
- Capture node → Evaluate node → conditional branch (store / dedup / HITL / reject)
- Add conditional edges based on evaluation scores
- Enable checkpointing so failures can be resumed

### Checkpoint
Send a test message like "I am an AI Engineer" and verify that a memory is extracted, evaluated, and stored in both databases.

---

## Phase 3: Retrieval & Explainability (2:30 – 3:15) — 45 minutes

### Retrieval Service (25 minutes)
Build the component that finds relevant memories when you ask a question.

How it works:
1. **Vector search:** Convert your question into an embedding and search ChromaDB for memories with similar mathematical representations
2. **Keyword search:** Search PostgreSQL for memories containing words from your question
3. **Fusion:** Combine both result sets using Reciprocal Rank Fusion, which gives each memory a blended score
4. **Re-ranking:** Sort by combined score, recency, confidence, and access frequency
5. **Top-k selection:** Return the best 5 memories

### Fallback handling:
If ChromaDB is unavailable (detected by repeated timeouts), the circuit breaker trips and the system uses only keyword search from PostgreSQL.

### Explainability Service (15 minutes)
Build the component that explains why each memory was retrieved.

For each retrieved memory, generate a plain-English explanation like:
> "This memory was retrieved because your question mentioned 'career advice' and this memory states you are an AI Engineer. The semantic similarity score is 92%. This memory was first recorded on January 15, 2026."

Include:
- Why it matched (semantic similarity, keyword overlap, or both)
- The relevance score
- When the memory was created
- How many times it has been used before

### Context Builder (5 minutes)
Format the retrieved memories into a structured context that the AI can read:
- List each memory with its explanation
- Organize by memory type
- Include confidence indicators

### Checkpoint
Ask a test question like "What should I learn next?" and verify that relevant memories are returned with explanations.

---

## Phase 4: Frontend Shell (3:15 – 3:45) — 30 minutes

### Chat Interface (15 minutes)
Build the main chat page:
- Message input box at the bottom
- Message history display (user messages on the right, assistant on the left)
- Send button that calls the backend chat API
- Loading indicator while waiting for response
- Display the assistant's response when it arrives

### Memory Sidebar (10 minutes)
Build a panel that shows alongside the chat:
- List of memories retrieved for the current question
- Each memory displayed as a card with its text and type
- Expandable explanation for why each memory was retrieved
- Visual distinction between semantic, procedural, and episodic memories

### Memory Management Page (5 minutes)
Build a simple table page:
- List all memories with columns: content, type, created date, status
- Delete button for each memory
- Basic styling

### Checkpoint
You can send a message, see a response, and see retrieved memories in the sidebar.

---

## Phase 5: Integration & Demo (3:45 – 4:00) — 15 minutes

### Integration (10 minutes)
- Connect the frontend chat to the backend chat endpoint
- Verify that sending a message triggers memory extraction
- Verify that the assistant's response includes retrieved memories
- Run through three test conversations:

| Test | What to Say | Expected Memory Stored |
|------|-------------|------------------------|
| Test 1 | "I am an AI Engineer" | Semantic: "User is an AI Engineer" |
| Test 2 | "I prefer first-principles explanations" | Procedural: "User prefers first-principles explanations" |
| Test 3 | "I built an AI CTO Agent in January" | Episodic: "User built an AI CTO Agent" |

### Demo Script (5 minutes)
Prepare a 3-minute walkthrough:
1. **Introduction:** "This is a memory system that learns about you across conversations"
2. **Test 1:** Type "I am an AI Engineer" — show the memory being extracted and stored
3. **Test 2:** Type "I prefer first-principles explanations" — show preference memory
4. **Test 3:** Type "I built an AI CTO Agent" — show episodic memory
5. **Retrieval demo:** Ask "What should I learn next?" — show relevant memories retrieved with explanations
6. **Governance demo:** Show the memory dashboard, delete a memory, show the audit log
7. **Failure mode mention:** Briefly explain how the system handles duplicates, outdated info, and service failures

### Final Checkpoint
- Demo runs smoothly in under 5 minutes
- All three memory types are demonstrated
- Retrieval with explanations works
- User can view and delete memories
- All 5 failure modes have at least basic mitigation implemented

---

## Risk Mitigation During Implementation

| Risk | What Could Go Wrong | Contingency Plan |
|------|---------------------|------------------|
| LangGraph too complex | Can't get workflow orchestration working in time | Fall back to simple sequential function calls |
| ChromaDB won't start | Vector database fails to initialize | Use in-memory mode for the demo; document the limitation |
| OpenAI API slow or rate-limited | Memory extraction takes too long | Cache embeddings; mock responses for demo if needed |
| Frontend not ready | UI components don't work in time | Use a command-line tool or API client for demo; ship backend only |
| Pipeline accuracy poor | Memories are wrong or irrelevant | Adjust evaluator thresholds; add more examples to AI instructions |

---

## Post-MVP Backlog (Prioritized)

1. **Human Review Queue UI** — Interface for reviewing low-confidence memories
2. **Memory Edit API** — Allow users to update memories, not just delete them
3. **Contradiction Detection** — Automatically detect when new facts conflict with old ones
4. **Full Circuit Breaker Implementation** — Complete resilience for all external services
5. **Audit Log Dashboard** — Visual audit trail in the frontend
6. **Metrics Dashboard** — Real-time charts for accuracy, latency, and usage
7. **Multi-User Support** — Tenant isolation and user authentication
8. **Memory Compression** — Summarize old episodic memories to save space
9. **A/B Testing Framework** — Compare different retrieval strategies
10. **Tiger Cloud Migration** — Consolidate PostgreSQL and ChromaDB into one managed service

---

## Definition of Done (MVP)

- [ ] User can send a message and receive a response
- [ ] System extracts at least one memory of each type (semantic, procedural, episodic) from demo conversations
- [ ] Memories are stored in both PostgreSQL and ChromaDB
- [ ] Retrieved memories are displayed with plain-English explanations
- [ ] User can view all memories in a dashboard
- [ ] User can delete memories
- [ ] All 5 failure modes have documented mitigation (at least basic implementation)
- [ ] Health check endpoint confirms all services are operational
- [ ] Demo script runs successfully in under 5 minutes

---

*Follows Agentic SWE Kit principles: engineering mindset, production readiness, and AI agent operations.*
