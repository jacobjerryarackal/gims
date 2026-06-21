from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.security import decode_access_token

security = HTTPBearer(auto_error=False)

async def get_current_user(request: Request):
    credentials = await security(request)
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload.get("sub")

async def optional_auth(request: Request):
    try:
        return await get_current_user(request)
    except:
        return None