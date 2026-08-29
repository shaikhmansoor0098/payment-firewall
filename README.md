# Payment Firewall — API

The backend half of the architecture described in the brief: a FastAPI service that takes a
message / screenshot text / decoded QR payload and returns a risk score, LOW/SUSPICIOUS/HIGH
classification, the reasons, and a recommendation — computed *before* any payment is authorized.

The interactive frontend prototype (all screens, demo mode, client-side QR decoding) ships as a
separate single-file React artifact. This service exists so the same risk-scoring logic is also
available as a real, runnable API — useful for a hackathon repo, a Swagger demo for judges, or
wiring up a real mobile/web client later.

## Project structure

```
backend/
├── app/
│   ├── main.py          FastAPI app + routes
│   ├── schemas.py        Pydantic request/response models (the AI JSON contract)
│   ├── mock_ai.py        AI analysis layer — deterministic stand-in, swap for a real API call
│   ├── risk_engine.py     Deterministic risk scoring — the only place risk_score is computed
│   └── demo_data.py      The three prepared demo scenarios
├── requirements.txt
├── .env.example
└── README.md
```

`mock_ai.py` and `risk_engine.py` are deliberately separate files (brief section 3): the mock
AI layer can be replaced with a real vision/LLM API call without touching how scores are
computed, and the risk engine never uses randomness — it only sums the weights of signals it
actually detected.

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in AI_API_KEY only if you wire up a real model call
uvicorn app.main:app --reload
```

The API is now running at `http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/docs` for
interactive Swagger docs — the fastest way to test it without a frontend.

## Endpoints

| Method | Path                    | Description                                              |
|--------|-------------------------|------------------------------------------------------------|
| GET    | `/api/health`           | Health check                                              |
| POST   | `/api/analyze`          | Analyze arbitrary text / amount / destination             |
| GET    | `/api/demo/{scenario}`  | Run a prepared scenario: `cashback`, `kyc`, or `cafe`      |

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"You have won ₹5,000 cashback. Scan this QR to receive your reward.","amount":5000,"destination":"cashback-reward@upi","direction":"SEND"}'
```

returns the structured verdict (`risk_score`, `risk_level`, `intent_mismatch`, `signals`,
`recommendation`, ...) matching the JSON contract in the product brief.

## Notes

- No secret keys are hardcoded anywhere — see `.env.example`.
- Image upload / OCR / QR decoding currently happen client-side in the frontend prototype
  (including a real on-device QR decode via the browser's `BarcodeDetector` API where
  supported). This backend focuses on the analysis + scoring contract; add an `/api/extract`
  endpoint backed by a real OCR/vision service if you need server-side extraction too.
- CORS is wide open (`*`) for local demo convenience — restrict `allow_origins` before any
  real deployment.
