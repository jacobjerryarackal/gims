from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from agents.pipeline import memory_pipeline
from services.governance_service import governance_service
from storage.postgres import postgres_storage
from core.exceptions import UserNotFoundException

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=4000)
    user_id: str = Field(...)
    conversation_id: Optional[str] = None
    memory_consent: bool = True

class ChatResponse(BaseModel):
    response: str
    memories_used: List[Dict[str, Any]] = []
    extracted_memories: List[Dict[str, Any]] = []
    latency_ms: int

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = datetime.utcnow()
    try:
        user_id = uuid.UUID(request.user_id)
        try:
            user = await governance_service.get_user(user_id)
        except UserNotFoundException:
            user = await governance_service.get_or_create_user(email=f"user_{request.user_id}@example.com", name="Demo User")
            user_id = user.id
        
        if request.conversation_id:
            conversation_id = uuid.UUID(request.conversation_id)
            try:
                conversation = await postgres_storage.get_conversation(conversation_id)
            except:
                conversation = await postgres_storage.create_conversation(user_id=user_id, title="New Conversation", memory_consent=request.memory_consent)
                conversation_id = conversation.id
        else:
            conversation = await postgres_storage.create_conversation(user_id=user_id, title="New Conversation", memory_consent=request.memory_consent)
            conversation_id = conversation.id
        
        pipeline_result = await memory_pipeline.process_message(user_id=user_id, conversation_id=conversation_id, message=request.message, role="user")
        
        context = pipeline_result.get("context", "")
        retrieved = pipeline_result.get("retrieved_memories", [])
        extracted = pipeline_result.get("stored_memories", [])
        
        if retrieved:
            memory_summary = "\n".join([f"- {m['content']}" for m in retrieved[:3]])
            response_text = f"I remember a few things about you:\n{memory_summary}\n\nBased on this context, here's my response to your message: '{request.message}'"
        else:
            response_text = f"I don't have any specific memories about you yet, but here's my response to: '{request.message}'"
        
        latency = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        return ChatResponse(response=response_text, memories_used=retrieved, extracted_memories=extracted, latency_ms=latency)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")