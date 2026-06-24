from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import uuid
from datetime import datetime

from services.governance_service import governance_service

router = APIRouter(tags=["audit"])


@router.get("")
async def get_audit_logs(
    user_id: str = Query(None),
    operation: str = Query(None),
    limit: int = Query(100),
    offset: int = Query(0)
):
    """Get audit logs."""
    try:
        if user_id:
            user_uuid = uuid.UUID(user_id)
            logs = await postgres_storage.get_audit_logs(user_id=user_uuid, limit=limit)
        else:
            logs = await postgres_storage.get_audit_logs(limit=limit)
        
        return {
            "items": [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "action": log.action,
                    "actor": log.actor,
                    "reason": log.reason,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ],
            "total": len(logs)
        }
    except Exception as e:
        print("AUDIT ERROR:", e)
        raise e

