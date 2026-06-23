export interface Memory {
  id: string;
  user_id: string;
  content: string;
  memory_type: "semantic" | "procedural" | "episodic";
  status: string;
  avg_score: number;
  created_at: string;
  expires_at: string | null;
}

export interface PaginatedMemories {
  memories: Memory[];
  total: number;
}

export interface RetrievedMemory {
  id: string;
  content: string;
  memory_type: string;
  similarity_score: number;
  retrieval_method: string;
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
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  memory_consent: boolean;
  is_active: boolean;
}

export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  actor: string;
  reason: string;
  created_at: string;
}

export interface HITLReview {
  id: string;
  memory_content: string;
  confidence_score: number;
  reason: string;
  status: string;
  created_at: string;
}

export interface SystemMetrics {
  retrieval_accuracy: number;
  memory_precision: number;
  memory_recall: number;
  duplicate_detection_rate: number;
  avg_latency_ms: number;
  memory_count: number;
  active_users: number;
}

export interface MemoryStats {
  total_memories: number;
  by_type: {
    semantic: number;
    procedural: number;
    episodic: number;
  };
  recently_added: number;
  active_memories: number;
}
