# ☕ TerraQuant — Autonomous Physical-to-Financial Commodity Risk Engine

> **Meta Global AI Developer Hackathon Submission**  
> **Tracks:** *Push the Frontier* & *Build for Your World*  
> **Creator:** Kailash Suthar (`832909-kkay`)

---

## 🚀 Executive Summary

Global supply-chain shocks don't begin on Wall Street; they begin on warehouse loading docks. By the time procurement desks review scanned PDF inspection reports, spot prices have already surged. **TerraQuant** is an autonomous multi-modal risk engine that bridges physical warehouse quality inspections directly to macro commodity risk modeling and enterprise procurement.

When a warehouse batch is inspected, TerraQuant segments physical defects down to the pixel, streams field audio, calculates econometric volatility shifts via stochastic modeling, and deploys verifiable agents to execute ERP penalties and derivatives hedges.

---

## 🛠️ Architecture & Meta Model Integration

TerraQuant chains multiple Meta AI models into an interdependent, closed-loop pipeline where each model's output directly parameterizes the next:

```
[Warehouse Video/Photo + Inspector Voice Note]
│
├──► SAM 3.1 (/v1/responses) ──► Pixel-level Defect / Spoilage Masking
├──► Muse Voice Transcribe (Realtime ASR) ──► Field Inspector Stream
▼
[Open-Weight Extraction Layer (Muse Spark Open / Glimmer-30B)]
│  Extracts structured physical grading & anomaly JSON
▼
[Deterministic Python Quant Engine (Modal / Local Sandbox)]
│  Fits GARCH(1,1) Volatility Model + Runs 10,000 Monte Carlo Paths
▼
[Muse Wonder 1.0 Verifiable Risk Agent (1M Context)]
├──► Cross-checks supplier SLA contracts & working capital caps
└──► Issues verified ERP Penalty Debit Notes & Strap Options Hedges
```

### 🧠 Meta AI Tooling Breakdown

1. **`SAM 3.1` (Vision Segmentation):** Isolates damaged seed clusters, foreign matter, and moisture clumping to calculate precise physical defect ratios.
2. **`Muse Voice Transcribe` (Realtime ASR):** Ingests live inspector voice memos to capture contextual warehouse notes.
3. **`Muse Spark 1.3` / Open-Weights:** Parses unstructured perception into strict JSON risk profiles.
4. **`Muse Wonder 1.0` (1M Context Orchestrator):** Executes parallel tool calling to audit contracts, verify accounting identities ($\text{Assets} = \text{Liabilities} + \text{Equity}$), and draft executive action cards.

---

## 📈 Quantitative & Financial Modeling

Unlike generic AI wrappers, TerraQuant converts computer vision metrics into rigorous financial mathematics:

* **GARCH(1,1) Volatility Calibration:** Fits econometric volatility clustering ($\omega, \alpha, \beta$) on historical daily commodity spot prices.
* **Physical Shock Multiplier:** Dynamically expands baseline volatility based on SAM 3.1 defect ratios:
  $$\sigma_{\text{shock}} = \sigma_{\text{baseline}} \times (1 + [\text{Defect Ratio} \times 2.5])$$
* **10,000-Path Monte Carlo Simulation:** Simulates 30-day delivery horizon price paths to compute 95% and 99% Value-at-Risk (VaR).
* **Verifiable Accounting Checker:** Automatically validates debit notes, working capital headroom, and derivative option strap premiums against treasury constraints.

---

## 💻 Tech Stack

* **Backend:** Python FastAPI, NumPy, Pandas, `arch` (GARCH econometric package), OpenCV.
* **Frontend:** React 19, Vite, Tailwind CSS v4, Lucide React, Recharts (Monte Carlo fan charts & distribution histograms).
* **Agentic Workflows:** Autonomous orchestration with smart neural simulation fallbacks.

---

## ⚙️ Quick Start & Local Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/832909-kkay/terraquant.git
   cd terraquant
   ```

2. **Install Dependencies:**
   ```bash
   # Python Virtual Environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r backend/requirements.txt

   # Frontend
   cd frontend
   npm install
   cd ..
   ```

3. **Configure Environment:**
   Copy the sample environment file and set your mock toggle:
   ```bash
   cp .env.example .env
   ```

4. **Launch Application:**
   - **Backend:**
     ```bash
     uvicorn backend.main:app --reload
     ```
     *(Runs on `http://localhost:8000`)*
   - **Frontend:**
     ```bash
     cd frontend && npm run dev
     ```
     *(Runs on `http://localhost:5173`)*

---

## 🏆 Hackathon Compliance & License

- Built 100% fresh during the Meta Global AI Developer Hackathon window (Oct 27 – Nov 4).
- Licensed under the [MIT License](LICENSE).

