# Meta Global AI Developer Hackathon — API Specification

## TerraQuant: Physical-to-Financial Commodity Risk Engine

---

## Environment Variables

| Variable | Description |
|---|---|
| `MODEL_API_KEY` | Meta AI API Key for model access |
| `META_BASE_URL` | Meta AI API base URL (`https://api.meta.ai/v1`) |
| `USE_MOCK` | When `True`, uses pre-recorded payloads instead of live API calls |

---

## Meta AI Models Used

### 1. SAM 3.1 — Segment Anything Model
- **Endpoint**: `POST /v1/responses`
- **Purpose**: Warehouse visual inspection — segment grain sacks, detect defects
- **Input**: Base64-encoded warehouse image
- **Output**: Bounding boxes + segmentation masks with defect labels

### 2. Muse Spark 1.3 — Structured Grading
- **Endpoint**: `POST /v1/chat/completions`
- **Model**: `muse-spark-1.3`
- **Purpose**: Structured JSON grading from SAM + voice transcript
- **Output**: `{ defect_pct, supply_shock_factor, sla_status }`

### 3. Muse Wonder 1.0 — Verifiable ERP Agent
- **Endpoint**: `POST /v1/chat/completions`
- **Model**: `muse-wonder-1.0`
- **Purpose**: Agentic SLA evaluation + financial action proposals
- **Output**: Penalty debit note, options strap hedge, verified accounting constraints

---

## Pipeline Flow

```
Warehouse Image + Inspector Voice
         │
         ▼
  SAM 3.1 (Segmentation)
         │
         ▼
  Muse Spark 1.3 (Grading)
         │
    defect_pct ──────────────────────────────────┐
         │                                        │
         ▼                                        ▼
  GARCH(1,1) on price history          Muse Wonder 1.0 (Agent)
         │                                        │
         ▼                                        ▼
  Monte Carlo 10k paths               SLA Validation + Hedge Proposal
         │                                        │
         ▼                                        ▼
  VaR (95%, 99%)              Accounting Constraint Checker
         │                                        │
         └──────────────── Dashboard ─────────────┘
```

---

## Backend Endpoints

### `POST /api/run-pipeline`
Runs the full TerraQuant pipeline end-to-end.

**Response:**
```json
{
  "sam_output": { "boxes": [...], "masks": [...] },
  "grading": { "defect_pct": 8.3, "supply_shock_factor": 1.21, "sla_status": "BREACH" },
  "voice_transcript": "...",
  "quant": {
    "var_95": 24500.0,
    "var_99": 31200.0,
    "fan_chart": { "p5": [...], "p25": [...], "p50": [...], "p75": [...], "p95": [...] },
    "histogram": [...]
  },
  "agent_action": {
    "penalty_debit_note": { ... },
    "hedge_proposal": { ... },
    "accounting_check": { "valid": true, "checks": [...] }
  }
}
```

### `POST /api/toggle-mock`
Toggles `USE_MOCK` between `True` and `False`.