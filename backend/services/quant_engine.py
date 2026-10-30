"""
TerraQuant — Quantitative Engine
GARCH(1,1) volatility estimation + Monte Carlo VaR simulation.
"""

import os
import sys

# Ensure single-threaded BLAS to avoid memory exhaustion
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from arch import arch_model

import config

logger = logging.getLogger(__name__)

# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class QuantResult:
    var_95: float
    var_99: float
    fan_chart: dict[str, list[float]]
    histogram: list[dict]
    garch_omega: float
    garch_alpha: float
    garch_beta: float
    baseline_vol: float
    adjusted_vol: float
    defect_ratio: float


# ── GARCH Fitting ─────────────────────────────────────────────────────────────

def fit_garch(returns: pd.Series) -> tuple[float, float, float, float]:
    """
    Fit GARCH(1,1) on log-return series.
    Returns (omega, alpha, beta, baseline_annualised_vol).
    """
    am = arch_model(returns * 100, vol="Garch", p=1, q=1, dist="normal", rescale=False)
    res = am.fit(disp="off", options={"maxiter": 500})
    params = res.params
    omega = float(params.get("omega", params.iloc[1]))
    alpha = float(params.get("alpha[1]", params.iloc[2]))
    beta  = float(params.get("beta[1]",  params.iloc[3]))
    last_var = float(res.conditional_volatility.iloc[-1]) ** 2  # variance (in % units)
    baseline_vol = float(res.conditional_volatility.iloc[-1]) / 100  # as decimal
    return omega, alpha, beta, baseline_vol


# ── Monte Carlo ────────────────────────────────────────────────────────────────

def run_monte_carlo(
    last_price: float,
    baseline_vol: float,
    defect_ratio: float,
    n_paths: int = config.MC_PATHS,
    horizon: int = config.MC_HORIZON,
) -> tuple[np.ndarray, float, float]:
    """
    Run Monte Carlo simulation with defect-adjusted volatility.
    Returns (paths array [horizon x n_paths], var_95, var_99).
    """
    adjusted_vol = baseline_vol * (1 + defect_ratio * config.DEFECT_VOL_MULTIPLIER)
    logger.info(
        f"Monte Carlo: baseline_vol={baseline_vol:.4f}, "
        f"defect_ratio={defect_ratio:.4f}, adjusted_vol={adjusted_vol:.4f}"
    )

    rng = np.random.default_rng(seed=42)
    daily_returns = rng.normal(
        loc=0.0,
        scale=adjusted_vol,
        size=(horizon, n_paths),
    )

    # Geometric Brownian price paths
    paths = np.zeros((horizon + 1, n_paths))
    paths[0] = last_price
    for t in range(1, horizon + 1):
        paths[t] = paths[t - 1] * np.exp(daily_returns[t - 1])

    final_prices = paths[-1]
    pnl = final_prices - last_price          # P&L per unit (MT)

    # VaR: worst losses (negative tail) scaled to 50 MT contract
    quantity = 50.0
    try:
        import json
        with config.SUPPLIER_SLA_JSON.open(encoding="utf-8") as f:
            sla_data = json.load(f)
            quantity = float(sla_data.get("contract_terms", {}).get("quantity_mt",
                             sla_data.get("contract_terms", {}).get("quantity_quintals", 50.0)))
    except Exception:
        quantity = 50.0

    var_95 = float(np.percentile(-pnl, 95)) * quantity
    var_99 = float(np.percentile(-pnl, 99)) * quantity

    return paths, var_95, var_99


# ── Fan chart builder ─────────────────────────────────────────────────────────

def build_fan_chart(paths: np.ndarray) -> dict[str, list[float]]:
    """Build percentile fan chart arrays over the simulation horizon."""
    days = list(range(paths.shape[0]))
    return {
        "days": days,
        "p5":  np.percentile(paths, 5,  axis=1).tolist(),
        "p25": np.percentile(paths, 25, axis=1).tolist(),
        "p50": np.percentile(paths, 50, axis=1).tolist(),
        "p75": np.percentile(paths, 75, axis=1).tolist(),
        "p95": np.percentile(paths, 95, axis=1).tolist(),
    }


def build_histogram(paths: np.ndarray, last_price: float, bins: int = 60) -> list[dict]:
    """Build histogram data for terminal price distribution."""
    final_prices = paths[-1]
    counts, edges = np.histogram(final_prices, bins=bins)
    result = []
    for i in range(len(counts)):
        mid = float((edges[i] + edges[i + 1]) / 2)
        result.append({"price": round(mid, 2), "count": int(counts[i])})
    return result


# ── Main entry point ──────────────────────────────────────────────────────────

def run_quant_engine(defect_pct: float) -> QuantResult:
    """
    Full quantitative pipeline:
      1. Load historical prices
      2. Fit GARCH(1,1)
      3. Run defect-adjusted Monte Carlo
      4. Compute VaR + fan chart + histogram
    """
    # 1. Load price data
    df = pd.read_csv(config.HISTORICAL_PRICES_CSV)
    date_col = next((c for c in df.columns if c.lower() in ("date", "timestamp")), df.columns[0])
    price_col = next((c for c in df.columns if c.lower() in ("close", "price_usd", "price")), df.columns[1])
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col).reset_index(drop=True)
    prices = df[price_col].astype(float)
    returns = np.log(prices / prices.shift(1)).dropna()
    last_price = float(prices.iloc[-1])

    # 2. Fit GARCH
    try:
        omega, alpha, beta, baseline_vol = fit_garch(returns)
    except BaseException as exc:
        logger.warning(f"GARCH fit failed ({exc}), using historical std as fallback")
        baseline_vol = float(returns.std())
        omega, alpha, beta = 0.175, 0.059, 0.909

    # 3. defect_ratio converts percentage → ratio (e.g. 8.3% → 0.083)
    defect_ratio = defect_pct / 100.0

    # 4. Monte Carlo
    paths, var_95, var_99 = run_monte_carlo(
        last_price=last_price,
        baseline_vol=baseline_vol,
        defect_ratio=defect_ratio,
    )
    adjusted_vol = baseline_vol * (1 + defect_ratio * config.DEFECT_VOL_MULTIPLIER)

    # 5. Outputs
    fan_chart = build_fan_chart(paths)
    histogram = build_histogram(paths, last_price)

    return QuantResult(
        var_95=round(var_95, 2),
        var_99=round(var_99, 2),
        fan_chart=fan_chart,
        histogram=histogram,
        garch_omega=round(omega, 6),
        garch_alpha=round(alpha, 4),
        garch_beta=round(beta, 4),
        baseline_vol=round(baseline_vol, 6),
        adjusted_vol=round(adjusted_vol, 6),
        defect_ratio=round(defect_ratio, 4),
    )
