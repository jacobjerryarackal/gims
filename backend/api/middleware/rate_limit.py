from fastapi import Request, HTTPException
import time
from collections import defaultdict

rate_limit_store = defaultdict(list)

async def rate_limit_middleware(request: Request, call_next):
    # Simple in-memory rate limiting
    client_ip = request.client.host
    now = time.time()
    
    # Clean old entries
    rate_limit_store[client_ip] = [t for t in rate_limit_store[client_ip] if now - t < 60]
    
    if len(rate_limit_store[client_ip]) > 60:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    rate_limit_store[client_ip].append(now)
    return await call_next(request)