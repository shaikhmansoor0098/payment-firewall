"""
MOCK AI ANALYSIS LAYER
-----------------------
Stands in for a real vision/LLM API call. It is deterministic and keyword-driven — NOT a
live model — but is written as a single entry point (`analyze`) with a fixed input/output
contract so it can be replaced by a real API call later without changing risk_engine.py or
main.py. That is the whole point of keeping this file separate (brief section 3).

To wire up a real provider: replace the body of `analyze()` with a call to your vision/LLM
API (e.g. using ANTHROPIC_API_KEY from the environment — see .env.example), prompt it to
return the same fields consumed by `Context` below, and leave everything else untouched.
"""

from .risk_engine import Context, detect_claimed_intent, run_risk_engine
from .schemas import AnalyzeRequest, AnalyzeResponse, Signal


def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    text = payload.text or ""
    direction = payload.direction or "SEND"
    claimed_intent = detect_claimed_intent(text)
    intent_mismatch = claimed_intent == "RECEIVE" and direction == "SEND"

    ctx = Context(
        text=text,
        amount=payload.amount,
        destination=payload.destination or "",
        claimed_intent=claimed_intent,
        direction=direction,
    )
    result = run_risk_engine(ctx)

    signals = [
        Signal(key=s.key, label=s.label, weight=s.weight, explanation=s.explanation)
        for s in result["fired"]
    ]

    if intent_mismatch:
        explanation = (
            f"The message implies you'll receive \u20b9{payload.amount:,.0f}, but this payment "
            f"actually sends \u20b9{payload.amount:,.0f} from your account."
            if payload.amount else
            "The message implies you'll receive money, but this payment actually sends money from your account."
        )
    elif signals:
        explanation = "Detected signals: " + ", ".join(s.label for s in signals) + "."
    else:
        explanation = "No risk signals detected in this transaction."

    return AnalyzeResponse(
        risk_score=result["score"],
        risk_level=result["level"],
        transaction_direction=direction,
        amount=payload.amount,
        destination=payload.destination,
        merchant=payload.merchant,
        claimed_intent=claimed_intent,
        actual_intent=direction,
        intent_mismatch=intent_mismatch,
        signals=signals,
        explanation=explanation,
        recommendation=result["recommendation"],
    )
