export type MemoryType = "semantic" | "procedural" | "episodic";

export interface Memory {
  id: string;
  user_id: string;
  conversation_id?: string;
  content: string;
  type: MemoryType;
  created_at: string;
  updated_at: string;
  last_retrieved_at?: string;
  retrieval_count: number;
  overall_score: number;
}

export interface PaginatedMemories {
  items: Memory[];
  total: number;
}

export interface MemoryStats {
  total: number;
  by_type: {
    semantic: number;
    procedural: number;
    episodic: number;
  };
  by_score_range: Record<string, number>;
  recently_added: Memory[];
  top_retrieved: Memory[];
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
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
  };
}

export interface RetrievedMemory {
  memory: Memory;
  similarity_score: number;
  explanation: string;
}