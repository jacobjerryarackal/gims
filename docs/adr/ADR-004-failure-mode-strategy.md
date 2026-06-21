# ADR-004: Failure Mode Strategy — Design Template + Failure Modes Framework

**Status:** Accepted | **Date:** 2026-06-21

---

## Context

The Design Template + Failure Modes framework teaches that every component in a system will eventually fail. The question is not *if* it fails, but *how safely* it fails. The AI PR Review Agent implements this with circuit breakers, retry policies, and human review queues. We must apply the same rigor to our memory system.

## Decision

We will implement a **four-layer defense** strategy:

### Layer 1: Prevention
Design components to fail less often in the first place:
- Quality gates block bad memories before they enter the system
- Deduplication prevents redundant storage
- Input validation catches malformed data early

### Layer 2: Detection
Monitor for failures in real-time:
- Audit logs record every operation
- Health checks verify all services are responding
- Metrics track accuracy, latency, and error rates

### Layer 3: Mitigation
When failures occur, the system degrades gracefully rather than crashing:
- If the vector database fails, fall back to keyword search
- If the AI model is slow, skip memory extraction and continue chatting
- If storage fails, queue the operation for retry

### Layer 4: Recovery
Automated or manual paths to restore full functionality:
- Retry failed operations with increasing delays
- Human review queue for uncertain decisions
- Automatic service restart on crash

## Failure Mode Mapping

| Failure Mode | Affected Component | How We Detect It | How We Mitigate It | What Happens If It Still Fails |
|--------------|-------------------|------------------|-------------------|--------------------------------|
| **Memory Pollution** | Extractor and Evaluator | Low accuracy scores, high user deletion rate | Quality gate blocks low-confidence memories; users can delete | Reject the memory and log the reason |
| **Duplicate Memories** | Storage and Deduplication | Similarity checks on insert | Semantic comparison before storage; merge or update existing | Flag for human review |
| **Wrong Retrieval** | Retrieval Service | Retrieval accuracy metric below 85% | Combine vector and keyword search; re-rank results | Fall back to keyword-only search |
| **Outdated Memories** | Governance Service | TTL expiration dates; user update requests | Auto-expire old memories; detect contradictions | Mark as stale and exclude from search |
| **Vector Search Failure** | ChromaDB | Connection timeouts; empty results | Circuit breaker stops hammering a dead service; switch to PostgreSQL keyword search | Use recent memories as fallback |

## Core Design Principles

1. **Every component fails gracefully.** The system should become slower but remain correct, not faster but wrong.

2. **The worst failure is a wrong answer delivered with confidence.** We prevent this with confidence thresholds and human review for uncertain cases.

3. **Feedback loops can poison themselves.** We prevent this by requiring minimum sample sizes, reviewing what the system learns, and letting old feedback fade in importance over time.

4. **High-stakes decisions need human oversight.** Memory storage has a confidence gate; anything uncertain goes to a person for review.

## Circuit Breaker Configuration

A circuit breaker is like a safety switch: if a service fails repeatedly, we stop calling it temporarily and use a backup instead.

| Service | Failure Threshold | Recovery Time | Backup Strategy |
|---------|------------------|---------------|-----------------|
| ChromaDB (vector search) | 5 failures in 1 minute | 60 seconds | Use PostgreSQL keyword search |
| OpenAI API (AI model) | 3 failures in 1 minute | 30 seconds | Skip memory extraction; use cached results |

## Retry Policy

When a temporary failure occurs, we retry with increasing delays:
- Try up to 3 times
- Wait 1 second, then 2 seconds, then 4 seconds between attempts
- If all retries fail, trigger the fallback strategy

## Why This Approach?

### Advantages
- **Resilient system:** Handles failures without losing data or giving wrong answers
- **Trustworthy:** Users can see why memories were stored or retrieved
- **Observable:** Every failure is logged; every fallback is traceable
- **Safe:** Wrong answers are caught before they reach the user

### Trade-offs
- **Complexity:** Adds retry, circuit breaker, and human review infrastructure
- **Latency:** Retries and review queues add delay (acceptable tradeoff for correctness)
- **Cost:** Human review requires person time (mitigated by high confidence thresholds)

## Related Documents
- `/docs/failure-modes/` — Detailed analysis of each failure mode
- ADR-003: How the pipeline handles failures at each step
- PRD Section 7: Non-Functional Requirements

---

*Follows the Design Template + Failure Modes framework: Step 4 (Failure Mode Analysis) and Step 5 (Prototype Scope).*
