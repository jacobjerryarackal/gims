from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import uuid
from datetime import datetime

from services.governance_service import governance_service

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("")
async def get_audit_logs(user_id: Optional[str] = Query(None), action: Optional[str] = Query(None), from_date: Optional[datetime] = Query(None), to_date: Optional[datetime] = Query(None), limit: int = 100):
    try:
        user_uuid = uuid.UUID(user_id) if user_id else None
        logs = await governance_service.get_audit_logs(user_id=user_uuid, action=action, limit=limit)
        return {"logs": [{"id": str(log.id), "action": log.action, "actor": log.actor, "created_at": log.created_at, "reason": log.reason} for log in logs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
