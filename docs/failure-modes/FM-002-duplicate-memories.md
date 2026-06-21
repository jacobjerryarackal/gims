# Failure Mode 2: Duplicate Memories

## What Are Duplicate Memories?

Duplicate memories happen when the same fact gets stored multiple times with slightly different wording. This wastes storage, confuses retrieval rankings, and makes the memory dashboard cluttered.

### Real Example

You mention your job in three different conversations:

| Conversation | What You Said | Stored As |
|-------------|-------------|-----------|
| Week 1 | "I am an AI Engineer" | "User is an AI Engineer" |
| Week 3 | "I work as an AI Engineer" | "User works as an AI Engineer" |
| Week 5 | "My job is AI Engineering" | "User's job is AI Engineering" |

All three mean the same thing, but the system stores them as three separate memories.

### Why This Happens

| Cause | Explanation |
|-------|-------------|
| **Semantic equivalence** | Different words, same meaning — the system doesn't understand they're the same |
| **Partial updates** | You restate a fact with additional detail, and the system treats it as new |
| **Extractor inconsistency** | The AI extracts the same fact differently on different days |
| **No central lookup** | The system doesn't check existing memories before storing new ones |

---

## How We Detect It

| Detection Method | How It Works | When It Triggers |
|------------------|-------------|------------------|
| **Pre-insertion similarity check** | Before storing, search for memories with similar meaning | Every new memory |
| **Fuzzy text matching** | Compare new text against existing text using approximate matching | Every new memory |
| **Temporal clustering** | Check for recent memories of the same type | Every new memory |

---

## How We Prevent It (Three Lines of Defense)

### Defense 1: Semantic Deduplication

Before storing any new memory, the system asks: "Do we already know something like this?"

It searches in two ways:
1. **Meaning-based search:** Looks for memories with similar mathematical representations (embeddings)
2. **Text-based search:** Looks for memories with similar words using fuzzy matching

If a very similar memory is found (similarity above 85%), the system doesn't create a duplicate. Instead, it decides whether to:
- **Update the existing memory** if the new version is more detailed or accurate
- **Reject the new memory** if the existing one is better
- **Merge them** if both contain unique information

### Defense 2: Merge Strategy

When two memories are found to be duplicates, the system keeps the best version:

| Scenario | Action | Example |
|----------|--------|---------|
| New memory has higher quality scores | Update existing with new content | "I am an AI Engineer" → "I am a Senior AI Engineer at OpenAI" |
| Existing memory has higher quality scores | Reject the new one | Keep "I am an AI Engineer," discard "I work as an AI Engineer" |
| Both contain unique details | Merge into one comprehensive memory | Combine "I am an AI Engineer" + "I work at OpenAI" → "I am an AI Engineer at OpenAI" |

The system preserves the history of changes, so you can see what the memory used to say.

### Defense 3: Uncertain Duplicates

If the similarity is unclear (between 70% and 85%):
- The memory is stored with a "pending review" status
- It's added to a deduplication log for manual review
- It doesn't appear in retrieval results until a human approves it

---

## What Happens When Prevention Fails

If deduplication is uncertain:
1. The memory is stored but marked as "pending review"
2. It doesn't show up in search results
3. A human reviewer checks the deduplication log
4. The reviewer decides: merge, keep separate, or delete

---

## How We Measure Success

| Metric | Target | What It Tells Us |
|--------|--------|----------------|
| **Duplicate Detection Rate** | 90%+ | How many true duplicates we catch |
| **False Positive Rate** | Under 5% | How many unique memories we incorrectly flag as duplicates |
| **Storage Efficiency** | Sub-linear growth | Memory count should grow slower than conversation count |

---

*Follows the Design Template + Failure Modes framework: every component must have a fallback, and the system should degrade to "slower but correct."*
