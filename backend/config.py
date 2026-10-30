"""
TerraQuant — Configuration
Loads .env and exposes typed settings.
"""

import os

# Limit BLAS threads to 1 to prevent memory over-allocation on constrained hosts
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"

from pathlib import Path
from dotenv import load_dotenv

# Resolve project root (backend/ is one level below root)
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)


def _bool(val: str | None) -> bool:
    return str(val).strip().lower() in ("true", "1", "yes")


# ── API credentials ──────────────────────────────────────────────────────────
MODEL_API_KEY: str = os.getenv("MODEL_API_KEY", "")
META_BASE_URL: str = os.getenv("META_BASE_URL", "https://api.meta.ai/v1").rstrip("/")

# ── Feature flags ─────────────────────────────────────────────────────────────
USE_MOCK: bool = _bool(os.getenv("USE_MOCK", "True"))

# ── Paths ────────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = BACKEND_DIR / "data"
MOCK_DATA_DIR = BACKEND_DIR / "mock_data"
HISTORICAL_PRICES_CSV = DATA_DIR / "historical_prices.csv"
SUPPLIER_SLA_JSON = DATA_DIR / "supplier_sla.json"

# ── Model names ───────────────────────────────────────────────────────────────
SAM_MODEL = "sam-3.1"
SPARK_MODEL = "muse-spark-1.3"
WONDER_MODEL = "muse-wonder-1.0"

# ── Quant parameters ─────────────────────────────────────────────────────────
MC_PATHS = 10_000
MC_HORIZON = 30          # days
DEFECT_VOL_MULTIPLIER = 2.5
VAR_95_PERCENTILE = 5
VAR_99_PERCENTILE = 1


def toggle_mock() -> bool:
    """Flip USE_MOCK in-process and persist to .env."""
    global USE_MOCK
    USE_MOCK = not USE_MOCK

    # Rewrite .env file
    lines = ENV_FILE.read_text().splitlines()
    new_lines = []
    found = False
    for line in lines:
        if line.startswith("USE_MOCK"):
            new_lines.append(f"USE_MOCK={'True' if USE_MOCK else 'False'}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"USE_MOCK={'True' if USE_MOCK else 'False'}")
    ENV_FILE.write_text("\n".join(new_lines) + "\n")

    return USE_MOCK
