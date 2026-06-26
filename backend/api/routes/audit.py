from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import uuid
from datetime import datetime
from storage.postgres import postgres_storage
from services.governance_service import governance_service

router = APIRouter(tags=["audit"])


@router.get("")
async def get_audit_logs(
    user_id: str = Query(None),
    action: str = Query(None),
    limit: int = Query(100),
    offset: int = Query(0)
):
    """Get audit logs."""
    try:
        user_uuid = uuid.UUID(user_id) if user_id else None
        logs = await governance_service.get_audit_logs(user_id=user_uuid, action=action, limit=limit, offset=offset)
        total = await governance_service.get_audit_log_count(user_id=user_uuid, action=action)

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
            "total": total
        }
    except Exception as e:
        print("AUDIT ERROR:", e)
        raise e

