from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime

from services.governance_service import governance_service

router = APIRouter(tags=["hitl"])


class HITLReviewRequest(BaseModel):
    action: str
    notes: Optional[str] = None


@router.get("/queue")
async def get_hitl_queue(status: str = "pending"):
    try:
        items = await governance_service.get_hitl_queue(status=status)
        return {
            "items": [
                {
                    "id": str(item.id),
                    "memory_content": item.memory.content if item.memory else item.reason,
                    "confidence_score": float(item.confidence_score),
                    "reason": item.reason,
                    "status": item.status,
                    "created_at": item.created_at
                }
                for item in items
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/{item_id}")
async def review_hitl_item(item_id: str, request: HITLReviewRequest):
    try:
        item_uuid = uuid.UUID(item_id)
        item = await governance_service.review_hitl_item(item_id=item_uuid, action=request.action, reviewer_notes=request.notes)
        return {"status": "success", "item_id": str(item.id), "action": request.action}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
