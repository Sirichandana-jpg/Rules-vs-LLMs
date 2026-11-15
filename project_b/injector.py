"""Corruption injector for the 12 problem types. inject(df, ptype, rate, rng) -> (corrupted_df, truth)
truth = {"rows": bool mask over corrupted_df rows that carry the defect (None = batch-level only), "batch": True, "detail": str}."""
import numpy as np, pandas as pd
from .schema import *

PTYPES = ["schema", "dtype", "datefmt", "latlon", "dup", "neardup", "nullspike", "closed_before", "zipboro", "pair", "resolution", "pii"]
NAMES = {"schema": "Renamed/dropped column", "dtype": "Column type change", "datefmt": "Date format switch", "latlon": "Lat/lon swapped",
         "dup": "Exact duplicates", "neardup": "Near-duplicates", "nullspike": "Null spike (one agency)", "closed_before": "Closed < created",
         "zipboro": "ZIP vs borough", "pair": "Complaint vs descriptor", "resolution": "Resolution vs status", "pii": "PII in free text"}
FIRST = ["Maria", "John", "Priya", "Wei", "Ahmed", "Sofia", "James"]; LAST = ["Gonzalez", "Smith", "Patel", "Chen", "Khan", "Rossi", "Brown"]


def _mask(n, idx):
    m = np.zeros(n, bool); m[idx] = True; return m


def inject(df, ptype, rate, rng):
    df = df.copy().reset_index(drop=True); n = len(df)
    k = max(1, int(rate * n))
    if ptype == "schema":
        col = rng.choice(["borough", "incident_zip", "created_date", "latitude", "status"])
        if rng.random() < .5: df = df.rename(columns={col: col.upper() + "_V2"}); d = f"renamed {col}"
        else: df = df.drop(columns=[col]); d = f"dropped {col}"
        return df, {"rows": None, "detail": d}
    if ptype == "dtype":
        col = rng.choice(["latitude", "longitude", "unique_key"]); df[col] = df[col].astype(str)
        return df, {"rows": None, "detail": f"{col} cast to string"}
    if ptype == "datefmt":
        cut = int(n * rng.uniform(.3, .7))
        df["created_date"] = df["created_date"].astype(object)
        df.loc[cut:, "created_date"] = pd.to_datetime(df.loc[cut:, "created_date"], format="mixed").dt.strftime(ALT_FMT).values
        return df, {"rows": _mask(n, np.arange(cut, n)), "detail": f"created_date switched to MM/DD/YYYY from row {cut}"}
    if ptype == "latlon":
        idx = rng.choice(np.where(df.latitude.notna())[0], k, replace=False)
        a, b = df.loc[idx, "latitude"].values.copy(), df.loc[idx, "longitude"].values.copy()
        df.loc[idx, "latitude"], df.loc[idx, "longitude"] = b, a
        return df, {"rows": _mask(n, idx), "detail": f"{k} rows swapped"}
    if ptype == "dup":
        src = df.iloc[rng.choice(n, k, replace=False)]; out = pd.concat([df, src], ignore_index=True)
        return out, {"rows": _mask(len(out), np.arange(n, n + k)), "detail": f"{k} exact copies appended"}
    if ptype == "neardup":
        src = df.iloc[rng.choice(n, k, replace=False)].copy()
        src["unique_key"] = df.unique_key.max() + 1 + np.arange(k)
        src["created_date"] = (pd.to_datetime(src["created_date"], format="mixed") + pd.to_timedelta(rng.integers(1, 30, k), "s")).dt.strftime(ISO_FMT).values
        alt = rng.integers(0, 3, k); d = src["descriptor"].astype(str).values
        src["descriptor"] = [x.upper() if a == 0 else (x + " ") if a == 1 else x[:-1] for x, a in zip(d, alt)]
        out = pd.concat([df, src], ignore_index=True)
        return out, {"rows": _mask(len(out), np.arange(n, n + k)), "detail": f"{k} near-duplicates (ts +1..30s, descriptor altered)"}
    if ptype == "nullspike":
        ag = df.agency.value_counts(); ag = ag[ag >= .03 * n].index
        a = rng.choice(list(ag)); col = rng.choice(["incident_zip", "borough", "descriptor", "complaint_type"])
        idx = np.where((df.agency == a).values & (rng.random(n) < .8))[0]; df.loc[idx, col] = np.nan
        return df, {"rows": _mask(n, idx), "detail": f"{col} nulled for {a}"}
    if ptype == "closed_before":
        idx = rng.choice(np.where(df.closed_date.notna())[0], k, replace=False)
        c = pd.to_datetime(df.loc[idx, "created_date"], format="mixed") - pd.to_timedelta(rng.integers(3600, 30 * 86400, k), "s")
        df.loc[idx, "closed_date"] = c.dt.strftime(ISO_FMT).values
        return df, {"rows": _mask(n, idx), "detail": f"{k} closed before created"}
    if ptype == "zipboro":
        idx = rng.choice(np.where(df.incident_zip.notna() & df.borough.isin(list(BORO_ZIPS)))[0], k, replace=False)
        new = [rng.choice(BORO_ZIPS[rng.choice([b for b in BORO_ZIPS if b != df.borough[i]])]) for i in idx]
        df.loc[idx, "incident_zip"] = new
        return df, {"rows": _mask(n, idx), "detail": f"{k} zips moved to another borough"}
    if ptype == "pair":
        by = df.groupby("complaint_type")["descriptor"].agg(lambda s: sorted(set(s.dropna()))).to_dict()
        idx = rng.choice(np.where(df.complaint_type.notna() & df.descriptor.notna())[0], k, replace=False)
        for i in idx:
            other = [t for t in by if t != df.complaint_type[i] and by[t]]
            df.loc[i, "descriptor"] = rng.choice(by[rng.choice(other)])
        return df, {"rows": _mask(n, idx), "detail": f"{k} descriptors from another complaint type"}
    if ptype == "resolution":
        idx = rng.choice(n, k, replace=False)
        for j, i in enumerate(idx):
            a = df.agency[i]
            if j % 2 == 0 and df.status[i] == "Closed": df.loc[i, "status"] = "Open"
            else:
                df.loc[i, "status"] = "Open"; df.loc[i, "resolution_description"] = CLOSED_RES[0].format(a=a)
        return df, {"rows": _mask(n, idx), "detail": f"{k} status/resolution contradictions"}
    if ptype == "pii":
        idx = rng.choice(n, k, replace=False); kinds = rng.integers(0, 4, k)
        for i, kd in zip(idx, kinds):
            ph = f"{rng.integers(200, 999)}-{rng.integers(200, 999)}-{rng.integers(1000, 9999)}"
            nm = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            em = f"{nm.lower().replace(' ', '.')}@example.com"
            extra = [f"Caller can be reached at {ph}.", f"Contact {em} for details.", f"Complainant {nm} requested a callback.", f"{nm}, {ph}, {em}."][kd]
            base = df.resolution_description[i]
            df.loc[i, "resolution_description"] = (base if isinstance(base, str) else "") + " " + extra
        return df, {"rows": _mask(n, idx), "detail": f"{k} rows with PII (phone/email/name mix)"}
    raise ValueError(ptype)
