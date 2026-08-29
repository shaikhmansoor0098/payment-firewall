"""
DETERMINISTIC RISK ENGINE
-------------------------
The only place a risk_score is produced. Purely additive over detected signals and capped
at 100 — never randomized (per brief section 9). Kept isolated from mock_ai.py so a real
AI/vision call can replace the signal-detection layer without touching scoring logic here.

Signal weights and detection rules are mirrored 1:1 with the frontend's SIGNAL_DEFS in
PaymentFirewall.jsx so both layers of the prototype agree on the same verdicts.
"""

import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

KNOWN_MERCHANTS = {"abc-cafe@upi", "chai-adda@upi", "bigbasket@upi", "irctc@upi", "swiggy@upi"}


@dataclass
class Context:
    text: str
    amount: Optional[float]
    destination: str
    claimed_intent: Optional[str]
    direction: str


@dataclass
class SignalDef:
    key: str
    label: str
    weight: int
    explanation: str
    detect: Callable[[Context], bool]


def _rx(pattern: str) -> Callable[[str], bool]:
    compiled = re.compile(pattern, re.IGNORECASE)
    return lambda text: bool(compiled.search(text or ""))


_is_threat = _rx(r"\b(block|suspend|freeze|deactivat|legal action|penalt|fine|seiz)")
_is_kyc = _rx(r"\bkyc\b|re-?verif|verify your (account|kyc|details)|update your (details|account)")
_is_urgent = _rx(r"urgent|immediat|\btoday\b|right now|expir|last chance|within \d+\s*(hour|min)")
_is_reward = _rx(
    r"cashback|reward|you'?ve won|congratulations|\bprize\b|\bbonus\b|refund of|lucky draw|"
    r"limited[- ]time offer|unlock your (discount|reward|cashback)"
)
_is_impersonation = _rx(
    r"customer care|customer support|bank (official|representative|team)|calling from|"
    r"your bank account|\brbi\b|income tax dept"
)


SIGNAL_DEFS: List[SignalDef] = [
    SignalDef(
        "mismatch", "Payment Direction Mismatch", 55,
        "The message implies you'll receive money, but this transaction actually sends money from your account.",
        lambda ctx: ctx.claimed_intent == "RECEIVE" and ctx.direction == "SEND",
    ),
    SignalDef(
        "threat", "Threat / Account Block Language", 18,
        "The message threatens account suspension, blocking, or legal action to pressure you into acting fast.",
        lambda ctx: _is_threat(ctx.text),
    ),
    SignalDef(
        "kyc", "KYC / Verification Manipulation", 18,
        "This uses a fake KYC or account-verification request \u2014 a very common scam pattern on UPI.",
        lambda ctx: _is_kyc(ctx.text),
    ),
    SignalDef(
        "urgency", "Urgency Pressure", 15,
        "Words like 'urgent', 'today', or 'immediately' create false time pressure so you act before thinking it through.",
        lambda ctx: _is_urgent(ctx.text),
    ),
    SignalDef(
        "reward", "Reward / Cashback Bait", 12,
        "The message baits you with a prize, cashback, or reward to lower your guard before the ask.",
        lambda ctx: _is_reward(ctx.text),
    ),
    SignalDef(
        "impersonation", "Impersonation of Bank / Authority", 12,
        "The message claims to be your bank or an official authority without any way to verify that.",
        lambda ctx: _is_impersonation(ctx.text),
    ),
    SignalDef(
        "unknown_recipient", "Unknown / Unverified Recipient", 10,
        "This payment goes to a UPI ID that isn't a recognized or previously used contact.",
        lambda ctx: bool(ctx.destination) and ctx.destination.lower() not in KNOWN_MERCHANTS,
    ),
    SignalDef(
        "unusual_amount", "Suspicious Micro-Payment", 5,
        "Scammers sometimes request tiny amounts (\u20b91\u2013\u20b910) first, just to confirm your UPI account is active.",
        lambda ctx: ctx.amount is not None and 0 < ctx.amount <= 10,
    ),
]


def detect_claimed_intent(text: str) -> Optional[str]:
    if not text:
        return None
    if re.search(r"receive|you'?ve won|cashback|refund of|congratulations|\bprize\b", text, re.IGNORECASE):
        return "RECEIVE"
    if re.search(r"\bsend\b|pay ₹|pay rs\.?|verify.*pay|scan.*pay", text, re.IGNORECASE):
        return "SEND"
    return None


def run_risk_engine(ctx: Context) -> Dict:
    score = 0
    fired: List[SignalDef] = []
    for sig in SIGNAL_DEFS:
        if sig.detect(ctx):
            score += sig.weight
            fired.append(sig)
    score = min(score, 100)
    if score >= 71:
        level = "HIGH"
    elif score >= 31:
        level = "SUSPICIOUS"
    else:
        level = "LOW"
    recommendation = {"HIGH": "DONT_PAY", "SUSPICIOUS": "VERIFY", "LOW": "PROCEED"}[level]
    return {"score": score, "level": level, "recommendation": recommendation, "fired": fired}
