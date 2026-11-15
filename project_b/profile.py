"""Task B1: profile the raw 2023 data for quality problems that already exist (counts + examples)."""
import re, json
import numpy as np, pandas as pd
from .schema import *
from .data import load_pool
from .detectors.base import s, ts
from .detectors.rules import PHONE, EMAIL


def ex(df, mask, n=3):
    return [int(k) for k in df.loc[mask, "unique_key"].head(n)]


def profile(df):
    n = len(df); out = []

    def add(issue, mask, note=""):
        mask = np.asarray(mask.fillna(False) if hasattr(mask, "fillna") else mask, bool)
        out.append({"issue": issue, "count": int(mask.sum()), "pct": round(100 * mask.mean(), 3), "example_unique_keys": ex(df, mask), "note": note})
    c, cl = ts(df, "created_date"), ts(df, "closed_date")
    add("Duplicate unique_key", df.unique_key.duplicated(keep=False), "primary key must be unique")
    add("Exact duplicate rows (all columns)", df.duplicated(keep=False))
    add("created_date outside calendar 2023 or unparsable", ~c.dt.year.eq(2023).fillna(False))
    add("closed_date earlier than created_date", cl < c)
    add("closed_date equals created_date (zero-length)", cl == c, "may be legitimate auto-close; check by agency")
    add("status=Closed but closed_date null", (df.status == "Closed") & df.closed_date.isna())
    add("closed_date present but status not Closed", df.closed_date.notna() & (df.status != "Closed"))
    add("latitude/longitude missing", df.latitude.isna() | df.longitude.isna())
    la, lo = df.latitude, df.longitude
    add("coordinates present but outside NYC bounding box", la.notna() & lo.notna() & ~(la.between(BBOX[0], BBOX[1]) & lo.between(BBOX[2], BBOX[3])))
    z = s(df, "incident_zip")
    add("incident_zip missing", z.isna())
    add("incident_zip not 5 digits", z.notna() & ~z.str.match(r"^\d{5}$"))
    exp = z.str.slice(0, 3).map(ZIP3_BORO); b = s(df, "borough")
    add("ZIP prefix implies different borough", exp.notna() & b.isin(list(BORO_ZIPS)) & (exp != b))
    add("borough = 'UNSPECIFIED'/missing", b.isna() | (b.str.upper() == "UNSPECIFIED"))
    t = s(df, "resolution_description").fillna("") + " " + s(df, "descriptor").fillna("")
    add("Phone/email pattern in free text", t.apply(lambda x: bool(PHONE.search(x) or EMAIL.search(x))), "possible PII leak")
    for col in ("complaint_type", "descriptor", "agency", "status"):
        v = s(df, col).dropna(); key = v.str.lower().str.strip()
        g = pd.DataFrame({"v": v, "k": key}).groupby("k")["v"].nunique()
        bad = set(g[g > 1].index)
        add(f"{col}: same value in different case/whitespace", pd.Series(key.isin(bad).reindex(df.index, fill_value=False)))
    for col in COLS:
        nr = df[col].isna().mean()
        if nr > .2: out.append({"issue": f"Column {col} mostly null", "count": int(df[col].isna().sum()), "pct": round(100 * nr, 2), "example_unique_keys": [], "note": ""})
    return out


if __name__ == "__main__":
    df, src = load_pool(); p = profile(df)
    from pathlib import Path
    Path(__file__).with_name("profile_b.json").write_text(json.dumps({"source": src, "rows": len(df), "issues": p}, indent=1))
    print(src, len(df)); [print(f"{i['count']:>8}  {i['pct']:>7}%  {i['issue']}") for i in p]
