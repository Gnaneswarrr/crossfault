"""Thin FastAPI backend for CrossFault."""

from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from crossfault.ai_layer import AIValidationError
from crossfault.service import InvestigationService

app = FastAPI(
    title="CrossFault API",
    description="Thin adapter exposing the bounded deterministic causal investigation pipeline.",
    version="0.1.0",
)

# We initialize a single service instance (lazy-loading the LLM client).
# Note: In a larger app, this might be injected via Depends().
_service = None

def get_service() -> InvestigationService:
    global _service
    if _service is None:
        _service = InvestigationService()
    return _service

@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}

@app.get("/api/investigate")
def investigate(scenario: str = "CF-001", seed: int = 48291):
    """
    Run the deterministic investigation and return the verified AI response.
    """
    if scenario not in ("CF-001", "CF-002"):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid scenario '{scenario}'. Must be 'CF-001' or 'CF-002'."
        )
        
    svc = get_service()
    
    try:
        response = svc.run_investigation(scenario_id=scenario, seed=seed)
        # We explicitly serialize the response to a dictionary using the to_dict() boundaries
        return JSONResponse(content=response.to_dict())
    except AIValidationError as e:
        # AI validation explicitly failed against deterministic bounds
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # Catch network/provider issues or unanticipated engine failures
        # Using 502 Bad Gateway for upstream LLM provider failures
        raise HTTPException(status_code=502, detail=str(e))
