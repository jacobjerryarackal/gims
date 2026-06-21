# Failure Mode 4: Outdated Memories

## What Are Outdated Memories?

Outdated memories happen when the system remembers facts about you that are no longer true. This causes the assistant to give advice based on old information, which can be embarrassing or counterproductive.

### Real Example

| When | What Was True | What the System Still Remembers |
|------|--------------|--------------------------------|
| 2023 | "I work at Google" | "I work at Google" |
| 2025 | You changed jobs to Anthropic | "I work at Google" (still stored!) |

When you ask for career advice in 2025, the assistant still thinks you work at Google.

### Why This Happens

| Cause | Explanation |
|-------|-------------|
| **No expiration mechanism** | Memories live forever by default |
| **No update pathway** | When you change a fact, the system doesn't know to update the old memory |
| **Temporal blindness** | The system doesn't track when a memory was created or how old it is |
| **No contradiction detection** | When you state a new fact that conflicts with an old one, the system doesn't notice |
| **User doesn't know to update** | You might not realize the system still remembers old information |

---

## How We Detect It

| Detection Method | How It Works | When It Triggers |
|------------------|-------------|------------------|
| **TTL expiration** | Each memory type has a time-to-live; old memories auto-expire | Based on memory age |
| **User updates** | Track how often users manually update or delete memories | Ongoing |
| **Contradiction detection** | New memories are checked against old ones for conflicts | Every new memory |
| **Stale memory report** | Users can mark memories as outdated | On user action |

---

## How We Prevent It (Three Lines of Defense)

### Defense 1: Time-To-Live (TTL) by Memory Type

Different types of memories become outdated at different rates:

| Memory Type | Default TTL | Reasoning |
|-------------|-------------|-----------|
| **Semantic (facts about you)** | 1 year | Facts like your job or location change occasionally |
| **Procedural (preferences)** | 3 months | Preferences change with seasons or new experiences |
| **Episodic (events)** | 1 month | Events fade in relevance quickly |

When a memory expires:
1. Its status changes to "stale"
2. It's excluded from retrieval results
3. The user is optionally notified: "I remember you worked at Google. Is this still true?"
4. If the user confirms it's still true, the TTL is extended

### Defense 2: Contradiction Detection

When a new memory is stored, the system checks: "Does this contradict anything we already know?"

| Scenario | Action | Example |
|----------|--------|---------|
| New fact contradicts old fact | Mark old as "replaced," link new as replacement | "I work at Anthropic" replaces "I work at Google" |
| New fact adds detail to old fact | Update old memory with new information | "I am an AI Engineer" → "I am a Senior AI Engineer" |
| New fact is unrelated | Store as separate memory | "I like hiking" doesn't affect "I work at Anthropic" |

The system preserves the relationship: you can see that "I work at Google" was replaced by "I work at Anthropic" on a specific date.

### Defense 3: User-Driven Updates

Users have full control to keep memories current:
- Edit any memory directly
- Delete outdated memories
- Mark memories as "still true" to extend their TTL
- See memory age and last-used date in the dashboard

---

## What Happens When Prevention Fails

If a stale memory is still active (missed by TTL or contradiction detection):
1. It's excluded from retrieval results
2. The system logs it as potentially stale
3. Optionally, the assistant asks: "I remember you worked at Google. Is this still accurate?"
4. The user's answer updates or confirms the memory

---

## How We Measure Success

| Metric | Target | What It Tells Us |
|--------|--------|----------------|
| **Stale Memory Rate** | Under 10% | How many active memories are outdated |
| **User Update Rate** | At least quarterly | Users actively maintain their memories |
| **Contradiction Detection** | 70%+ | How often we catch conflicting statements automatically |

---

*Follows the Design Template + Failure Modes framework: old feedback loses weight over time, and the system should decay outdated information.*
