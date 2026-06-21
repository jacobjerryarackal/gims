export interface Memory {
  id: string;
  user_id: string;
  type: "semantic" | "procedural" | "episodic";
  content: string;
  relevance_score: number;
  novelty_score: number;
  accuracy_score: number;
  overall_score: number;
  created_at: string;
  updated_at: string;
  expires_at: string | null;
  retrieval_count: number;
  last_retrieved_at: string | null;
  conversation_id: string | null;
  source_message: string | null;
  is_active: boolean;
}

export interface RetrievedMemory {
  memory: Memory;
  similarity_score: number;
  explanation: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  retrieved_memories?: RetrievedMemory[];
  metadata?: {
    processing_time_ms?: number;
    tokens_used?: number;
    memory_count?: number;
  };
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  is_memory_enabled: boolean;
}

export interface AuditLog {
  id: string;
  operation: "create" | "update" | "delete" | "retrieve" | "evaluate" | "extract";
  memory_id: string | null;
  user_id: string;
  details: Record<string, unknown>;
  created_at: string;
  ip_address: string | null;
  user_agent: string | null;
}

export interface HITLReview {
  id: string;
  memory_id: string;
  content: string;
  type: string;
  scores: {
    relevance: number;
    novelty: number;
    accuracy: number;
  };
  status: "pending" | "approved" | "rejected";
  reviewer_notes: string | null;
  created_at: string;
  reviewed_at: string | null;
}

export interface SystemMetrics {
  total_memories: number;
  total_conversations: number;
  total_messages: number;
  avg_retrieval_time_ms: number;
  memory_precision: number;
  memory_recall: number;
  duplicate_detection_rate: number;
  pending_reviews: number;
  api_health: {
    status: "healthy" | "degraded" | "down";
    latency_ms: number;
  };
  db_health: {
    status: "healthy" | "degraded" | "down";
    latency_ms: number;
  };
  vector_db_health: {
    status: "healthy" | "degraded" | "down";
    latency_ms: number;
  };
}

export interface MemoryStats {
  by_type: Record<string, number>;
  by_score_range: Record<string, number>;
  retrieval_frequency: Array<{ date: string; count: number }>;
  top_retrieved: Memory[];
  recently_added: Memory[];
}
