"""
Generate backend/data/historical_prices.csv
250 days of realistic daily Arabica coffee spot prices ~$300/quintal
with GARCH-style volatility clusters.
"""

import numpy as np
import pandas as pd
from pathlib import Path

OUTPUT = Path(__file__).parent / "historical_prices.csv"

np.random.seed(42)

n_days = 250
base_price = 300.0
mu = 0.0001          # slight upward drift

# GARCH-style volatility cluster simulation (stable α + β = 0.96 < 1)
omega = 0.000006
alpha = 0.08
beta  = 0.88
sigma2 = np.zeros(n_days)
sigma2[0] = 0.000225   # initial variance ~1.5% daily vol

eps = np.random.standard_normal(n_days)

log_returns = np.zeros(n_days)
log_returns[0] = mu + np.sqrt(sigma2[0]) * eps[0]

for t in range(1, n_days):
    sigma2[t] = omega + alpha * log_returns[t-1]**2 + beta * sigma2[t-1]
    # Occasional mild supply vol shock
    if np.random.rand() < 0.04:
        sigma2[t] *= np.random.uniform(1.4, 1.9)
    log_returns[t] = mu + np.sqrt(sigma2[t]) * eps[t]

# Reconstruct price series
prices = np.zeros(n_days)
prices[0] = base_price
for t in range(1, n_days):
    prices[t] = prices[t-1] * np.exp(log_returns[t])

# Keep realistic coffee bounds ($240–$360)
prices = np.clip(prices, 240, 360)

# Build date range (business days ending today)
end_date = pd.Timestamp("2026-10-29")
dates = pd.bdate_range(end=end_date, periods=n_days)

df = pd.DataFrame({
    "date": dates.strftime("%Y-%m-%d"),
    "price_usd": np.round(prices, 2),
    "log_return": np.round(log_returns, 6),
    "sigma": np.round(np.sqrt(sigma2), 6),
})

df.to_csv(OUTPUT, index=False)
print(f"Wrote {len(df)} rows to {OUTPUT}")
print(df.describe())
