"""
Payment Firewall API
---------------------
Run locally with:   uvicorn app.main:app --reload
Interactive docs:    http://127.0.0.1:8000/docs

Flow: request -> mock_ai.analyze() [AI layer] -> risk_engine.run_risk_engine() [scoring] ->
structured AnalyzeResponse. The two layers are intentionally separate files so the AI layer
can be swapped for a real model/API call without touching the risk engine (brief section 3).
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from demo_data import DEMO_SCENARIOS
from .mock_ai import analyze
from .schemas import AnalyzeRequest, AnalyzeResponse

app = FastAPI(
    title="Payment Firewall API",
    version="0.1.0",
    description="Pre-payment scam detection: analyzes a message, screenshot text, or QR payload "
                "and returns a risk score, classification, and reasons — before any payment is authorized.",
)

# Wide-open CORS for local hackathon/demo use. Tighten allow_origins before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze_endpoint(payload: AnalyzeRequest):
    """Analyze a message / screenshot text / decoded QR payload and return a risk verdict."""
    if not payload.text and payload.amount is None and not payload.destination:
        raise HTTPException(
            status_code=400,
            detail="No payment information could be extracted. Provide text, an amount, or a destination.",
        )
    return analyze(payload)


@app.get("/api/demo/{scenario}", response_model=AnalyzeResponse)
def demo(scenario: str):
    """Run one of the three prepared demo scenarios: cashback | kyc | cafe."""
    if scenario not in DEMO_SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Unknown scenario '{scenario}'. Choose: cashback, kyc, cafe.")
    return analyze(DEMO_SCENARIOS[scenario])
