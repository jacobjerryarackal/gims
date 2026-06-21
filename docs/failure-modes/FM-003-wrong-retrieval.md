# Failure Mode 3: Wrong Retrieval

## What Is Wrong Retrieval?

Wrong retrieval happens when the system brings up memories that aren't relevant to your current question, or misses memories that would have been helpful. This makes the assistant's responses less useful or even misleading.

### Real Example

You ask: "What should I learn next?"

| What Should Happen | What Actually Happens |
|-------------------|----------------------|
| Retrieve: "User is an AI Engineer" (relevant for career advice) | Retrieved: "User prefers first-principles explanations" (somewhat relevant) |
| Retrieve: "User built an AI CTO Agent" (relevant for project suggestions) | Missed: "User is an AI Engineer" (most relevant for learning recommendations) |
| | Retrieved: "User's favorite color is blue" (completely irrelevant) |

### Why This Happens

| Cause | Explanation |
|-------|-------------|
| **Vector search limitations** | "Similar meaning" doesn't always mean "relevant to the question" |
| **Missing keyword context** | Domain-specific terms might not be captured by meaning-based search |
| **Recency bias** | Old memories ranked too high or too low |
| **Query misunderstanding** | The AI misinterprets what you're actually asking |
| **Keyword-only search** | Exact word matching misses related concepts |

---

## How We Detect It

| Detection Method | How It Works | When It Triggers |
|------------------|-------------|------------------|
| **Retrieval accuracy metric** | Manual evaluation: for 20 test queries, did the top 3 results contain at least one relevant memory? | Weekly |
| **User feedback** | Thumbs up / thumbs down on retrieved memories | Every retrieval |
| **Latency monitoring** | If retrieval takes too long, quality may have degraded | Every retrieval |
| **Empty result checks** | Unexpected empty results may indicate search failure | Every retrieval |

---

## How We Prevent It (Three Lines of Defense)

### Defense 1: Hybrid Search Strategy

Instead of relying on one search method, we combine two:

| Search Method | What It Does Best | Example |
|---------------|-------------------|---------|
| **Semantic (meaning-based)** | Finds conceptually related memories | You ask about "career" and it finds "I am an AI Engineer" |
| **Keyword (word-based)** | Finds exact matches for specific terms | You mention "CTO Agent" and it finds that exact project |

The system runs both searches in parallel, then combines the results using a technique called Reciprocal Rank Fusion. This gives each memory a combined score from both methods.

### Defense 2: Smart Re-Ranking

After getting candidate memories from both searches, the system re-ranks them using multiple signals:

| Signal | Weight | Explanation |
|--------|--------|-------------|
| **Semantic similarity** | High | How closely the memory matches the query in meaning |
| **Keyword relevance** | Medium | How many query words appear in the memory |
| **Recency** | Medium | Newer memories are often more relevant |
| **Access frequency** | Low | Memories you've referenced before may be more important |
| **Confidence score** | Medium | Higher-quality memories are preferred |

### Defense 3: LLM Re-Ranking

For the top candidate memories, the system asks the AI: "How relevant is each of these to the user's question?"

The AI returns a relevance score and explanation for each candidate, allowing for nuanced judgment that pure mathematical search can't provide.

---

## Fallback: When Vector Search Fails

If the vector database becomes unavailable (detected by repeated failures), the system:
1. Stops trying the vector database for 60 seconds (circuit breaker)
2. Switches to keyword-only search using PostgreSQL
3. Logs the fallback for monitoring
4. Continues operating with potentially less accurate but still functional retrieval

---

## How We Measure Success

| Metric | Target | What It Tells Us |
|--------|--------|----------------|
| **Retrieval Accuracy** | 85%+ | Top results contain relevant memories |
| **Mean Reciprocal Rank** | 0.75+ | Relevant memories appear near the top |
| **User Satisfaction** | 80%+ thumbs-up | Users find retrieved memories helpful |

---

*Follows the Design Template + Failure Modes framework: the system degrades to "slower but correct" rather than "fast but wrong."*
