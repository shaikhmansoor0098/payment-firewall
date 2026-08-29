"""
Pydantic request/response models.

AnalyzeResponse mirrors the structured AI-output contract described in the product brief
(section 10) so the frontend, the mock AI layer, and a future real model call all agree on
one shape.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    source: str = Field(default="message", description="qr | screenshot | message")
    text: Optional[str] = Field(default="", description="Raw message / screenshot text, if any")
    amount: Optional[float] = Field(default=None, description="Payment amount in INR")
    destination: Optional[str] = Field(default=None, description="UPI ID / VPA the payment goes to")
    merchant: Optional[str] = Field(default=None, description="Merchant / payee display name, if known")
    direction: Optional[str] = Field(default="SEND", description="SEND | RECEIVE — what the transaction itself does")


class Signal(BaseModel):
    key: str
    label: str
    weight: int
    explanation: str


class AnalyzeResponse(BaseModel):
    risk_score: int
    risk_level: str  # LOW | SUSPICIOUS | HIGH
    transaction_direction: str
    amount: Optional[float] = None
    destination: Optional[str] = None
    merchant: Optional[str] = None
    claimed_intent: Optional[str] = None  # RECEIVE | SEND | None
    actual_intent: str
    intent_mismatch: bool
    signals: List[Signal]
    explanation: str
    recommendation: str  # DONT_PAY | VERIFY | PROCEED
