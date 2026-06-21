# ADR-005: Security & Governance Architecture

**Status:** Accepted | **Date:** 2026-06-21

---

## Context

A memory system stores personal, potentially sensitive information about users. This includes their job, preferences, habits, and life events. We must design for security and privacy from the very beginning, following the AI PR Review Agent's security principles and the Agentic SWE Kit security-engineering guidelines.

## Decision

We will implement a **defense-in-depth** security model with multiple protective layers:

### Layer 1: Data Protection

| Protection | How It Works |
|------------|-------------|
| **Encryption at rest** | All data stored in the database is encrypted by the cloud provider (Railway) |
| **Encryption in transit** | All communication between frontend and backend uses secure HTTPS connections |
| **Secret management** | API keys and passwords are stored in environment variables, never in the code |
| **PII handling** | Memory content is treated as personal information; audit logs don't store the raw content |

### Layer 2: Access Control

| Control | How It Works |
|---------|-------------|
| **API Authentication** | Every request from the frontend carries a secure token that proves who you are |
| **User Isolation** | Every memory record is tagged with your user ID; you can only see your own memories |
| **Admin Protection** | Administrative functions require additional authentication |

### Layer 3: Governance Controls

| Control | How It Works | Why It Matters |
|---------|-------------|---------------|
| **Consent Management** | Each conversation asks if you want memories stored; you can say no | Respects user autonomy |
| **Retention Policy** | Memories automatically expire after a set time (configurable by type) | Prevents infinite data accumulation |
| **Deletion Rights** | You can permanently delete any memory at any time | GDPR "right to be forgotten" compliance |
| **Audit Trail** | Every memory operation is logged with who did it, when, and why | Accountability and debugging |
| **Export Rights** | You can request a copy of all your data | Data portability compliance |

### Layer 4: Input Safety

| Control | How It Works |
|---------|-------------|
| **Input sanitization** | All user messages are cleaned before processing to prevent manipulation attacks |
| **Rate limiting** | Each user can only send a limited number of messages per minute to prevent abuse |
| **Message length limits** | Messages are capped at a reasonable length to prevent resource exhaustion |

## Security Threat Model

| Threat | How Likely | How Bad | How We Prevent It |
|--------|-----------|---------|-------------------|
| Someone tricks the AI into extracting false memories | Likely | Moderate | Input sanitization, accuracy scoring, human review |
| Someone steals memory data | Moderate | Severe | Encryption, user isolation, audit logs, least privilege |
| API keys leak | Moderate | Severe | Environment variables, regular rotation |
| Someone floods the system with fake messages | Low | Moderate | Rate limiting, maximum memory count per user |
| AI hallucinates false facts in extraction | Likely | Moderate | Evaluator gate, confidence thresholds, human review |

## Why This Security Model?

### Advantages
- **Compliance-ready:** Meets GDPR and CCPA requirements for deletion, audit, and consent
- **Trustworthy:** Users can see and control their own data
- **Secure by design:** No need for retroactive security patches

### Trade-offs
- **Complexity:** Adds authentication, audit, and consent infrastructure
- **Latency:** Audit logging adds a small delay to write operations (handled asynchronously)
- **User friction:** Consent prompts may interrupt the flow (mitigated by one-time consent per session)

## Related Documents
- PRD Section 6: Functional Requirements (Feature 6: Governance)
- `/docs/schemas/database-schema.sql` — Audit log table design

---

*Follows Agentic SWE Kit: security-engineering and production-readiness principles.*
