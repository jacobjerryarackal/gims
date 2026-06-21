-- ============================================================
-- GIMS Database Schema
-- GPT Intelligence Memory System
-- PostgreSQL + ChromaDB Hybrid Architecture
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- For fuzzy text matching
CREATE EXTENSION IF NOT EXISTS "vector";        -- If using pgvector (optional, ChromaDB primary)

-- ============================================================
-- 1. USERS & AUTHENTICATION
-- ============================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    name            VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    consent_given   BOOLEAN NOT NULL DEFAULT FALSE,  -- GDPR consent flag
    preferences     JSONB DEFAULT '{}'               -- User-level preferences
);

CREATE INDEX idx_users_email ON users(email);

-- ============================================================
-- 2. CONVERSATIONS
-- ============================================================

CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(500),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    memory_consent  BOOLEAN NOT NULL DEFAULT TRUE,   -- Per-conversation consent
    metadata        JSONB DEFAULT '{}'
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);

-- ============================================================
-- 3. CONVERSATION TURNS (Messages)
-- ============================================================

CREATE TABLE conversation_turns (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    token_count     INT,
    metadata        JSONB DEFAULT '{}'
);

CREATE INDEX idx_turns_conversation_id ON conversation_turns(conversation_id);
CREATE INDEX idx_turns_created_at ON conversation_turns(created_at);

-- ============================================================
-- 4. MEMORIES (Core Entity)
-- ============================================================

CREATE TYPE memory_type AS ENUM ('semantic', 'procedural', 'episodic');
CREATE TYPE memory_status AS ENUM ('active', 'stale', 'deleted', 'pending_review');

CREATE TABLE memories (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    memory_type     memory_type NOT NULL,
    content         TEXT NOT NULL,                    -- The actual memory text
    content_vector  VECTOR(1536),                     -- Optional: if using pgvector backup

    -- Evaluation scores
    relevance_score NUMERIC(3,2) NOT NULL CHECK (relevance_score BETWEEN 0 AND 1),
    novelty_score   NUMERIC(3,2) NOT NULL CHECK (novelty_score BETWEEN 0 AND 1),
    accuracy_score  NUMERIC(3,2) NOT NULL CHECK (accuracy_score BETWEEN 0 AND 1),
    avg_score       NUMERIC(3,2) GENERATED ALWAYS AS (
        (relevance_score + novelty_score + accuracy_score) / 3
    ) STORED,

    -- Storage & lifecycle
    status          memory_status NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,                      -- TTL for auto-expiration
    access_count    INT NOT NULL DEFAULT 0,           -- How many times retrieved
    last_accessed_at TIMESTAMPTZ,

    -- Episodic-specific fields
    event_date      DATE,                             -- For episodic memories
    participants    TEXT[],                          -- For episodic memories

    -- Metadata
    source_turn_id  UUID REFERENCES conversation_turns(id),
    metadata        JSONB DEFAULT '{}',
    chroma_id       VARCHAR(255),                   -- Reference to ChromaDB document ID

    -- Constraints
    CONSTRAINT chk_episodic_fields CHECK (
        (memory_type != 'episodic') OR 
        (event_date IS NOT NULL AND participants IS NOT NULL)
    )
);

-- Indexes
CREATE INDEX idx_memories_user_id ON memories(user_id);
CREATE INDEX idx_memories_user_type ON memories(user_id, memory_type);
CREATE INDEX idx_memories_status ON memories(status) WHERE status = 'active';
CREATE INDEX idx_memories_created_at ON memories(created_at);
CREATE INDEX idx_memories_expires_at ON memories(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_memories_avg_score ON memories(avg_score);

-- Full-text search index for keyword retrieval fallback
CREATE INDEX idx_memories_content_fts ON memories 
    USING GIN (to_tsvector('english', content));

-- Trigram index for fuzzy matching (duplicate detection)
CREATE INDEX idx_memories_content_trgm ON memories 
    USING GIN (content gin_trgm_ops);

-- ============================================================
-- 5. MEMORY RELATIONSHIPS (Graph Structure for Future)
-- ============================================================

CREATE TABLE memory_relationships (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    target_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,           -- e.g., 'replaces', 'relates_to', 'contradicts'
    confidence      NUMERIC(3,2) NOT NULL DEFAULT 0.5,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source_memory_id, target_memory_id, relationship_type)
);

CREATE INDEX idx_relationships_source ON memory_relationships(source_memory_id);
CREATE INDEX idx_relationships_target ON memory_relationships(target_memory_id);

-- ============================================================
-- 6. MEMORY DEDUPLICATION LOG
-- ============================================================

CREATE TABLE memory_dedup_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    new_memory_id   UUID NOT NULL REFERENCES memories(id),
    existing_memory_id UUID NOT NULL REFERENCES memories(id),
    similarity_score NUMERIC(3,2) NOT NULL,
    action_taken    VARCHAR(50) NOT NULL,           -- 'merged', 'rejected', 'flagged'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dedup_new ON memory_dedup_log(new_memory_id);
CREATE INDEX idx_dedup_existing ON memory_dedup_log(existing_memory_id);

-- ============================================================
-- 7. RETRIEVAL LOG (For evaluation & debugging)
-- ============================================================

CREATE TABLE retrieval_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query           TEXT NOT NULL,
    query_embedding VECTOR(1536),                     -- Optional backup
    retrieved_memory_ids UUID[] NOT NULL,
    retrieval_method VARCHAR(50) NOT NULL,             -- 'vector', 'keyword', 'hybrid'
    latency_ms      INT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata        JSONB DEFAULT '{}'                -- Relevance scores, explanations
);

CREATE INDEX idx_retrieval_logs_user_id ON retrieval_logs(user_id);
CREATE INDEX idx_retrieval_logs_created_at ON retrieval_logs(created_at);

-- ============================================================
-- 8. MEMORY AUDIT LOG (Governance & Compliance)
-- ============================================================

CREATE TABLE memory_audit_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_id       UUID REFERENCES memories(id) ON DELETE SET NULL,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action          VARCHAR(50) NOT NULL,             -- 'created', 'updated', 'deleted', 'retrieved', 'expired'
    actor           VARCHAR(50) NOT NULL,             -- 'system', 'user', 'extractor_agent', 'evaluator_agent'
    old_value       JSONB,                            -- Previous state (for updates)
    new_value       JSONB,                            -- New state
    reason          TEXT,                             -- Why this action occurred
    ip_address      INET,                             -- For security tracking
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_memory_id ON memory_audit_log(memory_id);
CREATE INDEX idx_audit_user_id ON memory_audit_log(user_id);
CREATE INDEX idx_audit_action ON memory_audit_log(action);
CREATE INDEX idx_audit_created_at ON memory_audit_log(created_at);

-- ============================================================
-- 9. HITL QUEUE (Human-in-the-Loop)
-- ============================================================

CREATE TABLE hitl_queue (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_id       UUID REFERENCES memories(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason          TEXT NOT NULL,                    -- Why it needs review
    confidence_score NUMERIC(3,2) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    reviewer_notes  TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at     TIMESTAMPTZ
);

CREATE INDEX idx_hitl_user_id ON hitl_queue(user_id);
CREATE INDEX idx_hitl_status ON hitl_queue(status) WHERE status = 'pending';

-- ============================================================
-- 10. SYSTEM HEALTH & METRICS
-- ============================================================

CREATE TABLE system_metrics (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name     VARCHAR(100) NOT NULL,
    metric_value    NUMERIC(10,4) NOT NULL,
    labels          JSONB DEFAULT '{}',
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_metrics_name_time ON system_metrics(metric_name, recorded_at);

-- ============================================================
-- 11. TRIGGER: Auto-update updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 12. TRIGGER: Audit log on memory changes
-- ============================================================

CREATE OR REPLACE FUNCTION log_memory_change()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO memory_audit_log (memory_id, user_id, action, actor, new_value, reason)
        VALUES (NEW.id, NEW.user_id, 'created', 'system', row_to_json(NEW), 'Memory extracted and stored');
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO memory_audit_log (memory_id, user_id, action, actor, old_value, new_value, reason)
        VALUES (NEW.id, NEW.user_id, 'updated', 'system', row_to_json(OLD), row_to_json(NEW), 'Memory updated');
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO memory_audit_log (memory_id, user_id, action, actor, old_value, reason)
        VALUES (OLD.id, OLD.user_id, 'deleted', 'system', row_to_json(OLD), 'Memory deleted');
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER memory_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON memories
    FOR EACH ROW EXECUTE FUNCTION log_memory_change();

-- ============================================================
-- 13. VIEW: Active Memories with Metadata
-- ============================================================

CREATE VIEW active_memories AS
SELECT 
    m.*,
    u.email as user_email,
    c.title as conversation_title,
    CASE 
        WHEN m.expires_at IS NOT NULL AND m.expires_at < NOW() THEN TRUE 
        ELSE FALSE 
    END as is_expired
FROM memories m
JOIN users u ON m.user_id = u.id
LEFT JOIN conversations c ON m.conversation_id = c.id
WHERE m.status = 'active';

-- ============================================================
-- 14. VIEW: Memory Health Dashboard
-- ============================================================

CREATE VIEW memory_health AS
SELECT 
    user_id,
    memory_type,
    COUNT(*) as total_count,
    AVG(avg_score) as avg_quality_score,
    COUNT(*) FILTER (WHERE expires_at < NOW()) as expired_count,
    COUNT(*) FILTER (WHERE status = 'pending_review') as pending_review_count,
    MAX(created_at) as last_memory_created
FROM memories
GROUP BY user_id, memory_type;

-- ============================================================
-- SEED DATA (For Demo)
-- ============================================================

INSERT INTO users (id, email, name, consent_given) VALUES
    ('550e8400-e29b-41d4-a716-446655440000', 'demo@example.com', 'Demo User', TRUE);

INSERT INTO conversations (id, user_id, title, memory_consent) VALUES
    ('660e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', 'Demo Conversation', TRUE);

-- Sample memories for testing retrieval
INSERT INTO memories (user_id, conversation_id, memory_type, content, relevance_score, novelty_score, accuracy_score, status) VALUES
    ('550e8400-e29b-41d4-a716-446655440000', '660e8400-e29b-41d4-a716-446655440000', 'semantic', 'User is an AI Engineer', 0.95, 0.90, 0.95, 'active'),
    ('550e8400-e29b-41d4-a716-446655440000', '660e8400-e29b-41d4-a716-446655440000', 'procedural', 'User prefers first-principles explanations', 0.90, 0.85, 0.88, 'active'),
    ('550e8400-e29b-41d4-a716-446655440000', '660e8400-e29b-41d4-a716-446655440000', 'episodic', 'User built an AI CTO Agent', 0.92, 0.88, 0.90, 'active');

-- Update episodic memory with required fields
UPDATE memories SET event_date = '2026-01-15', participants = ARRAY['User'] 
WHERE content = 'User built an AI CTO Agent';
