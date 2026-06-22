from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from agents.pipeline import memory_pipeline
from services.governance_service import governance_service
from storage.postgres import postgres_storage
from core.exceptions import UserNotFoundException

router = APIRouter(tags=["chat"])

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=4000)
    user_id: str = Field(...)
    conversation_id: Optional[str] = None
    memory_consent: bool = True

class ConversationCreateRequest(BaseModel):
    user_id: str = Field(...)
    memory_consent: bool = True

class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None
    memories_used: List[Dict[str, Any]] = []
    extracted_memories: List[Dict[str, Any]] = []
    latency_ms: int

@router.get("/conversations")
async def get_conversations(user_id: str = Query(...)):  # user_id must be provided as query param
    """Get all conversations for a user."""
    try:
        user_uuid = uuid.UUID(user_id)
        conversations = await postgres_storage.get_conversations_by_user(user_uuid)
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@router.post("/conversations")
async def create_conversation(request: ConversationCreateRequest):
    try:
        user_id = uuid.UUID(request.user_id)
        try:
            user = await governance_service.get_user(user_id)
        except UserNotFoundException:
            user = await governance_service.get_or_create_user(
                email=f"user_{request.user_id}@example.com",
                name="Demo User"
            )
            user_id = user.id

        conversation = await postgres_storage.create_conversation(
            user_id=user_id,
            title="New Conversation",
            memory_consent=request.memory_consent
        )
        return {
            "conversation_id": str(conversation.id),
            "title": conversation.title,
            "user_id": str(user_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str):
    """Get all messages in a conversation."""
    try:
        conv_uuid = uuid.UUID(conversation_id)
        turns = await postgres_storage.get_conversation_turns(conv_uuid)
        return {"messages": turns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    try:
        conv_uuid = uuid.UUID(conversation_id)
        await postgres_storage.delete_conversation(conv_uuid)
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

@router.post("")  # This handles POST /api/chat
async def send_message(request: ChatRequest):
    """Send a message and get a response."""
    start_time = datetime.utcnow()
    try:
        user_id = uuid.UUID(request.user_id)
        try:
            user = await governance_service.get_user(user_id)
        except UserNotFoundException:
            user = await governance_service.get_or_create_user(
                email=f"user_{request.user_id}@example.com", 
                name="Demo User"
            )
            user_id = user.id
        
        if request.conversation_id:
            conversation_id = uuid.UUID(request.conversation_id)
            try:
                conversation = await postgres_storage.get_conversation(conversation_id)
            except:
                conversation = await postgres_storage.create_conversation(
                    user_id=user_id,
                    title="New Conversation",
                    memory_consent=request.memory_consent
                )
                conversation_id = conversation.id
        else:
            conversation = await postgres_storage.create_conversation(
                user_id=user_id,
                title="New Conversation",
                memory_consent=request.memory_consent
            )
            conversation_id = conversation.id
        
        pipeline_result = await memory_pipeline.process_message(
            user_id=user_id,
            conversation_id=conversation_id,
            message=request.message,
            role="user"
        )
        
        context = pipeline_result.get("context", "")
        retrieved = pipeline_result.get("retrieved_memories", [])
        extracted = pipeline_result.get("stored_memories", [])
        
        if retrieved:
            memory_summary = "\n".join([f"- {m['content']}" for m in retrieved[:3]])
            response_text = f"I remember a few things about you:\n{memory_summary}\n\nBased on this context, here's my response to your message: '{request.message}'"
        else:
            response_text = f"I don't have any specific memories about you yet, but here's my response to: '{request.message}'"
        
        latency = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        return ChatResponse(
            response=response_text,
            conversation_id=str(conversation_id),
            memories_used=retrieved,
            extracted_memories=extracted,
            latency_ms=latency
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")