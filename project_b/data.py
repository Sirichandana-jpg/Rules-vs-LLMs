import numpy as np, pandas as pd
from pathlib import Path
from .schema import COLS
from .synth_311 import synth
RAW = Path(__file__).parent.parent / "data" / "raw_2023.csv"


def standardize(df):
    df = df.copy()
    for c in COLS:
        if c not in df: df[c] = np.nan
    df = df[COLS]
    df["incident_zip"] = df["incident_zip"].astype("string").str.slice(0, 5).astype(object).where(df["incident_zip"].notna(), np.nan)
    df["borough"] = df["borough"].astype("string").str.upper().astype(object).where(df["borough"].notna(), np.nan)
    for c in ("latitude", "longitude"): df[c] = pd.to_numeric(df[c], errors="coerce")
    df["unique_key"] = pd.to_numeric(df["unique_key"], errors="coerce").astype("int64")
    for c in ("created_date", "closed_date"):
        df[c] = df[c].astype("string").str.slice(0, 19).str.replace(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})$", r"\1.000", regex=True).astype(object).where(df[c].notna(), np.nan)
    return df.reset_index(drop=True)


def load_pool():
    """-> (DataFrame, provenance string). Real data if data/raw_2023.csv exists, else clearly-labelled synthetic."""
    if RAW.exists():
        return standardize(pd.read_csv(RAW, dtype=str)), "REAL: NYC 311 Service Requests, created in calendar year 2023 (NYC Open Data erm2-nwe9)"
    return synth(), "SYNTHETIC offline smoke data (NOT real NYC 311) - run `python -m project_b.fetch_311` then re-run for real numbers"


def batches(df, n_batches, size, rng):
    for _ in range(n_batches):
        yield df.iloc[np.sort(rng.choice(len(df), size, replace=False))].reset_index(drop=True)
