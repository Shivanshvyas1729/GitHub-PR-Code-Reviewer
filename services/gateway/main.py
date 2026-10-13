from httpx import _status_codes
from fastapi import status
import hashlib
import hmac
import httpx
from fastapi import FastAPI, HTTPException, Request
from prometheus_fastapi_instrumentator import Instrumentator
from models import Settings


settings = Settings()
app = FastAPI(title="Gateway Service")

# Expose Prometheus /metrics endpoint for monitoring
# Instrumentator().instrument(app).expose(app)

@app.get("/health")
async def health():
    return {"status":"ok"}

# take the . meta. payload from req
#2. compute SHA256 of that body and compare with what the github sent to me in req.  
#3. forward it to internal webhook serive using httpx

# 4. Use a constant-time comparison

@app.post("/webhook/github")
async def github_webhook(request: Request):

    body = await request.body()
    received_signature = request.headers.get("X-hub-Signature-256")

    if not received_signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing signature header"
        )


    expected_signature = 'sha256=' + hmac.new(
        settings.github_webhook_secret.encode(), 
        body, 
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, received_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid Signature")
    


    
    # 5. Prepare headers to forward to internal service
    # Replicates GitHub headers so downstream service knows the exact event type
    forward_headers = {
        "Content-Type": request.headers.get("Content-Type", "application/json"),
        "X-GitHub-Event": request.headers.get("X-GitHub-Event", ""),
        "X-GitHub-Delivery": request.headers.get("X-GitHub-Delivery", "")
    }

    # 6. Forward payload asynchronously
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://webhook:8001/events",
                content=body,
                headers=forward_headers,
                timeout=10.0 # Good practice: add a timeout so it doesn't hang forever
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Handle downstream 4xx/5xx failures cleanly
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Downstream service returned error: {e.response.status_code}"
            )
        except httpx.RequestError:
            # Handle downstream network/connection failures
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Downstream service unavailable"
            )

    return {"status": "ok"}