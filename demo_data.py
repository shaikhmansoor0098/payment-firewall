"""Ready-to-use demo scenarios (brief section 14), exposed via GET /api/demo/{scenario}."""

from .schemas import AnalyzeRequest

DEMO_SCENARIOS = {
    "cashback": AnalyzeRequest(
        source="qr",
        text="Congratulations! You've won ₹5,000 cashback. Scan this QR code to receive your money.",
        amount=5000,
        destination="cashback-reward@upi",
        merchant="Unknown \u00b7 Reward Promotion",
        direction="SEND",
    ),
    "kyc": AnalyzeRequest(
        source="screenshot",
        text="Your bank account will be blocked today. Send ₹2,999 immediately to verify your KYC.",
        amount=2999,
        destination="kyc-verify-support@upi",
        merchant="Unknown \u00b7 Claims to be your bank",
        direction="SEND",
    ),
    "cafe": AnalyzeRequest(
        source="qr",
        text="",
        amount=450,
        destination="abc-cafe@upi",
        merchant="ABC Caf\u00e9",
        direction="SEND",
    ),
}
