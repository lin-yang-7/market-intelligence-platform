# AI Engine MVP

The AI Engine provides deterministic MVP inference for opportunity scoring,
risk scoring, confidence scoring, and explanations. It is intentionally model
agnostic so a trained model can replace the rule scorer without changing the
online API contract.

## Local Run

```powershell
$env:PYTHONPATH='backend/common;ai-engine'
uvicorn ai_engine.app.main:app --host 0.0.0.0 --port 8010
```

## API

- `GET /health`
- `POST /v1/ai/predict`
- `POST /v1/ai/explain`
- `GET /v1/ai/model`
