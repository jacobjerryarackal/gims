export type MemoryType = "semantic" | "procedural" | "episodic";

export interface Memory {
  id: string;
  user_id: string;
  conversation_id?: string;
  content: string;
  type: MemoryType;
  status: string;
  created_at: string;
  updated_at: string;
  last_retrieved_at?: string;
  retrieval_count: number;
  overall_score: number;
  expires_at: string | null;
}

export interface PaginatedMemories {
  items: Memory[];               // was: memories
  total: number;
}

export interface RetrievedMemory {
  memory: Memory;                // nested Memory object
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
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;          // added
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
  total: number;                  // was: total_memories
  by_type: {
    semantic: number;
    procedural: number;
    episodic: number;
  };
  recently_added: Memory[];       // was: number — now array of Memory
  top_retrieved: Memory[];        // added
  by_score_range?: Record<string, number>;  // added
  active_memories?: number;       // optional
}