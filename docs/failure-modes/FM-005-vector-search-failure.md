# Failure Mode 5: Vector Search Failure

## What Is Vector Search Failure?

Vector search failure happens when the system that stores and searches memory meanings (ChromaDB) becomes unavailable, slow, or returns corrupted results. Since semantic search is a core feature, this can severely impact the system's usefulness.

### Real Example

You ask: "What projects have I worked on?"

| Normal Behavior | Failure Behavior |
|-----------------|------------------|
| System finds: "I built an AI CTO Agent" (semantic match) | System returns: No results found |
| System finds: "I created a memory system" (related concept) | System returns: Empty or random results |
| Response time: 200ms | Response time: Timeout or 10+ seconds |

### Why This Happens

| Cause | Explanation |
|-------|-------------|
| **Network issues** | The vector database server can't be reached |
| **Data corruption** | The embedding index becomes damaged |
| **Resource exhaustion** | The server runs out of memory or CPU |
| **Version mismatch** | The client and server speak different protocols |
| **Too many requests** | The database is overwhelmed and drops connections |

---

## How We Detect It

| Detection Method | How It Works | When It Triggers |
|------------------|-------------|------------------|
| **Health checks** | Regular "are you alive?" pings to the vector database | Every 30 seconds |
| **Timeout monitoring** | If a search takes longer than 200ms, something is wrong | Every search |
| **Empty result validation** | Unexpected empty results may indicate corruption | Every search |
| **Error rate tracking** | If more than 5% of searches fail, alert the team | Ongoing |

---

## How We Prevent It (Three Lines of Defense)

### Defense 1: Circuit Breaker

A circuit breaker is like a safety switch in your home electrical system. If the vector database fails repeatedly, we "trip the breaker" and stop calling it for a while.

| Failure Count | Action | Duration |
|---------------|--------|----------|
| 1-4 failures | Retry with increasing delays | Up to 10 seconds |
| 5 failures in 1 minute | Trip circuit breaker | Stop calling for 60 seconds |
| After 60 seconds | Test with one request | If successful, resume normal operation |
| Still failing after test | Alert admin, continue with fallback | Until manually fixed |

This prevents the system from "hammering" a dead service, which would make recovery harder.

### Defense 2: Fallback Cascade

When vector search fails, the system tries alternatives in order:

| Fallback Level | Method | Quality | When Used |
|----------------|--------|---------|-----------|
| **Primary** | Vector search (ChromaDB) | Best | Normal operation |
| **Fallback 1** | Keyword search (PostgreSQL) | Good | Circuit breaker is open |
| **Fallback 2** | Recent memories only | Basic | Both primary and fallback 1 fail |
| **Last resort** | No memories | Minimal | Everything fails |

The system never fully stops working — it just becomes less sophisticated.

### Defense 3: Graceful Degradation UX

When using a fallback, the system notes this internally but doesn't burden the user with technical details. However, if retrieval quality is significantly degraded, the assistant might say:

> "I'm working with limited memory access right now, so my context might not be as complete as usual."

This sets appropriate expectations without requiring technical knowledge.

---

## Recovery Process

| Step | Action | Who Does It |
|------|--------|-------------|
| 1 | Circuit breaker tests if the service is back | Automatic |
| 2 | If successful, resume normal vector search | Automatic |
| 3 | If still failing, alert the administrator | Automatic |
| 4 | Admin investigates logs and restarts/repairs the service | Human |
| 5 | If data is corrupted, rebuild the vector index from PostgreSQL | Automatic script |

---

## How We Measure Success

| Metric | Target | What It Tells Us |
|--------|--------|----------------|
| **Vector Database Uptime** | 99.5%+ | How often the service is healthy |
| **Fallback Usage Rate** | Under 1% | How often we need backups |
| **Recovery Time** | Under 5 minutes | How fast we restore full functionality |
| **User Impact** | Zero service outages | Users never see a complete failure |

---

*Follows the Design Template + Failure Modes framework: external systems have their own reliability, so we design for graceful degradation when they fail.*
