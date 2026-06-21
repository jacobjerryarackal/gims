# ADR-003: Memory Pipeline Orchestration — LangGraph

**Status:** Accepted | **Date:** 2026-06-21

---

## Context

Our memory system has a 6-step pipeline:
1. **Capture** — Extract candidate memories from the conversation
2. **Evaluate** — Score each candidate for quality
3. **Store** — Save approved memories to the database
4. **Retrieve** — Find relevant memories for the current question
5. **Context Builder** — Format memories for the AI to use
6. **LLM** — Generate the final response with memory context

Some steps can run in parallel (like extracting multiple memories from one message), while others must happen in sequence (you can't retrieve memories before storing them). We also need to handle failures at any step without losing work.

The AI PR Review Agent uses LangGraph to manage its parallel specialist agents. We will use the same approach for our pipeline.

## Decision

We will use **LangGraph** to orchestrate the memory pipeline. It provides:
- **Checkpointing:** If a step fails, we can resume from where we left off
- **Parallel execution:** Multiple memory extractions can happen simultaneously
- **Conditional branching:** Different paths based on evaluation scores
- **Observability:** Every step is traceable and logged

## The Pipeline Flow

```
[START]
   |
   v
[CAPTURE] — The Extractor reads the conversation and identifies facts worth remembering
   |
   v
[EVALUATE] — The Evaluator scores each fact on relevance, novelty, and accuracy
   |
   +-- High Score (above 0.85) ----------> [STORE] — Save directly to database
   |
   +-- Medium Score (0.70 to 0.85) ------> [DEDUP CHECK] — Check if we already know this
   |                                         |
   |                                         +-- New fact --> [STORE]
   |                                         +-- Duplicate --> [MERGE or SKIP]
   |
   +-- Low Score (0.50 to 0.70) ---------> [HITL QUEUE] — Queue for human review
   |
   +-- Very Low Score (below 0.50) -------> [REJECT] — Log and discard
   |
   v
[RETRIEVE] — Search for memories relevant to the user's current question
   |
   v
[CONTEXT BUILDER] — Format retrieved memories into a clear context for the AI
   |
   v
[LLM] — Generate the response using the memory context
   |
   v
[END]
```

## What Each Step Does

| Step | Input | Output | What Happens |
|------|-------|--------|--------------|
| **Capture** | The user's message | A list of candidate memories | The Extractor identifies facts, preferences, and events |
| **Evaluate** | Candidate memories | Scored memories with pass/fail/queue decisions | The Evaluator judges quality on three dimensions |
| **Store** | Approved memories | Stored memories with IDs | Save to PostgreSQL and ChromaDB |
| **Dedup Check** | Medium-confidence memories | Decision to merge, update, or store | Compare against existing memories for similarity |
| **HITL Queue** | Low-confidence memories | Queue entry for human review | A person decides whether to keep or discard |
| **Reject** | Very low-confidence memories | Audit log entry | Log why it was rejected |
| **Retrieve** | The user's current question | Relevant memories with scores | Search both databases and rank results |
| **Context Builder** | Retrieved memories | Formatted context string | Prepare memories for the AI to read |
| **LLM** | Context + current question | Final response | Generate the answer using memory context |

## Conditional Routing Logic

After evaluation, each memory follows one of four paths based on its quality score:

| Average Score | Path | Reasoning |
|---------------|------|-----------|
| Above 0.85 | Direct to Storage | High confidence — safe to store automatically |
| 0.70 to 0.85 | Duplicate Check | Good but might already exist — verify first |
| 0.50 to 0.70 | Human Review | Uncertain — needs a person to decide |
| Below 0.50 | Reject | Too uncertain — don't risk storing bad data |

## Why LangGraph?

### Advantages
- **Resilient:** If a step fails, we can resume without redoing everything
- **Observable:** Every node execution is traceable
- **Extensible:** Easy to add new steps later (like memory compression or cross-referencing)
- **Testable:** Each step can be tested independently

### Trade-offs
- **Learning curve:** Team needs to understand how state flows through the graph
- **Overhead:** For a simple 6-step pipeline, the orchestration might seem like overkill (but it pays off when we add more features)
- **Debugging:** Graph execution can be harder to trace than linear code (mitigated by detailed logging)

## Alternatives We Considered

| Alternative | Why We Didn't Choose It |
|-------------|------------------------|
| Celery task chains | No built-in checkpointing; harder to visualize the flow |
| Pure async/await | No built-in state management; we'd have to build our own |
| Prefect or Dagster | Too heavy for a 4-hour hackathon |
| Custom state machine | We'd be reinventing what LangGraph already does well |

## Related Documents
- ADR-001: Overall architecture style
- ADR-004: How failures are handled at each step
- `/docs/backlog/implementation-plan.md` — Hour-by-hour build plan

---

*Follows Agentic SWE Kit: llmops-ai-agents and distributed-systems principles.*
