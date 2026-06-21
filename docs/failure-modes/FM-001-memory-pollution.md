# Failure Mode 1: Memory Pollution

## What Is Memory Pollution?

Memory pollution happens when the system stores incorrect, irrelevant, or fabricated information about you. This is the most dangerous failure because wrong memories actively mislead the assistant and erode trust.

### Real Example

You say: "My friend is an AI Engineer and works at Google."

The system incorrectly stores: "User is an AI Engineer at Google."

Weeks later, when you ask for career advice, the assistant assumes you work at Google — which is completely wrong.

### Why This Happens

| Cause | Explanation |
|-------|-------------|
| **AI hallucination** | The AI model invents facts that weren't in your message |
| **Pronoun confusion** | The system can't tell whether "he," "she," or "they" refers to you or someone else |
| **Over-extraction** | The system treats passing mentions as permanent facts |
| **Context misinterpretation** | A joke or hypothetical is taken as a real statement |

---

## How We Detect It

| Detection Method | How It Works | When It Triggers |
|------------------|-------------|------------------|
| **Quality Gate** | Every candidate memory is scored on accuracy before storage | Every extraction |
| **Novelty Check** | If a memory seems too similar to existing ones, it's flagged for review | During storage |
| **Audit Sampling** | A random 5% of stored memories are manually reviewed weekly | Ongoing |
| **Deletion Rate Tracking** | If users frequently delete memories, something is wrong | Ongoing |

---

## How We Prevent It (Three Lines of Defense)

### Defense 1: Extraction Hardening

The memory extractor is given strict instructions:
- Only extract facts the user explicitly stated about themselves
- Never infer information that wasn't directly said
- Use exact quotes when possible
- If uncertain, don't extract — it's better to miss a fact than store a false one
- Distinguish between "you said X" and "your friend said X"

### Defense 2: The Evaluator Gate

Before any memory is stored, it passes through a quality checkpoint:

| Score Range | What Happens | Why |
|-------------|-------------|-----|
| **Above 0.85** | Store automatically | High confidence — safe to save |
| **0.70 to 0.85** | Check for duplicates first | Good quality, but might already exist |
| **0.50 to 0.70** | Queue for human review | Uncertain — needs a person to decide |
| **Below 0.50** | Reject and log | Too uncertain — risk of pollution is too high |

The evaluator checks three dimensions:
- **Relevance:** Is this actually useful to remember later?
- **Novelty:** Is this new information, or do we already know it?
- **Accuracy:** Is this fact likely to be correct based on the source text?

### Defense 3: User Governance

Even if a bad memory slips through, users have full control:
- View all memories in a dashboard
- One-click delete with full audit trail
- "Report incorrect" button feeds back to improve the evaluator
- Bulk delete option for cleaning up

---

## What Happens When Prevention Fails

If the evaluator's confidence is too low:
1. The memory is **NOT stored**
2. The rejection is logged in the audit trail with the reason
3. The conversation continues normally without the memory
4. Optionally, the system can ask the user: "Should I remember that you're an AI Engineer?" (human-in-the-loop)

---

## How We Measure Success

| Metric | Target | What It Tells Us |
|--------|--------|----------------|
| **False Memory Rate** | Under 5% | How often wrong memories get stored |
| **User Deletion Rate** | Under 10% | How often users remove stored memories |
| **HITL Queue Size** | Under 10% of extractions | Whether the extractor is appropriately conservative |

---

*Follows the Design Template + Failure Modes framework: every component must fail gracefully, and the worst failure is a wrong answer delivered with confidence.*
