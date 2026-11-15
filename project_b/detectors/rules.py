"""Family (a): declarative rules / schema checks. Each returns Alert. No learning except the curated pair allow-list."""
import re
import numpy as np, pandas as pd
from .base import *
PHONE = re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
OPEN_ST = {"Open", "Pending", "In Progress", "Assigned", "Started"}


def schema(df, ref):
    miss, extra = sorted(set(COLS) - set(df.columns)), sorted(set(df.columns) - set(COLS))
    return Alert(flag=bool(miss or extra), msg=f"missing={miss} unexpected={extra}", explain=2)


def dtype(df, ref):
    bad = [c for c in NUMERIC_COLS if c in df and not pd.api.types.is_numeric_dtype(df[c])]
    return Alert(flag=bool(bad), msg=f"non-numeric dtype in {bad} (expected numeric)", explain=2)


def datefmt(df, ref):
    m = np.zeros(len(df), bool)
    for c in ("created_date", "closed_date"):
        x = s(df, c); m |= nummask(x.notna() & ~x.str.match(ISO_RE))
    return Alert(mask=m, msg=f"{m.sum()} date strings not ISO-8601 (YYYY-MM-DDThh:mm:ss)", explain=2)


def latlon(df, ref):
    la, lo = pd.to_numeric(df.get("latitude"), errors="coerce"), pd.to_numeric(df.get("longitude"), errors="coerce")
    ok = la.between(BBOX[0], BBOX[1]) & lo.between(BBOX[2], BBOX[3])
    m = nummask(la.notna() & lo.notna() & ~ok)
    return Alert(mask=m, msg=f"{m.sum()} coordinates outside NYC bbox {BBOX}", explain=2)


def dup(df, ref):
    m = df.duplicated(keep="first").values
    return Alert(mask=m, msg=f"{m.sum()} rows identical to an earlier row", explain=2)


def neardup(df, ref):
    t = ts(df, "created_date")
    key = s(df, "agency").fillna("") + "|" + s(df, "complaint_type").fillna("") + "|" + s(df, "incident_address").str.lower().str.strip().fillna("") + "|" + s(df, "incident_zip").fillna("")
    o = pd.DataFrame({"k": key, "t": t}).reset_index().sort_values(["k", "t"])
    gap = o.groupby("k")["t"].diff().dt.total_seconds()
    m = np.zeros(len(df), bool); m[o.loc[(gap < 60).values, "index"].values] = True
    return Alert(mask=m, msg=f"{m.sum()} rows repeat (agency,type,address,zip) within 60s of an earlier row", explain=2)


def nullspike(df, ref):
    m = np.zeros(len(df), bool)
    for c in REQUIRED:
        if c in df: m |= df[c].isna().values
    return Alert(mask=m, msg=f"{m.sum()} nulls in required columns {REQUIRED}", explain=2)


def closed_before(df, ref):
    m = nummask(ts(df, "closed_date") < ts(df, "created_date"))
    return Alert(mask=m, msg=f"{m.sum()} rows with closed_date < created_date", explain=2)


def zipboro(df, ref):
    exp = s(df, "incident_zip").str.slice(0, 3).map(ZIP3_BORO)
    b = s(df, "borough"); m = nummask(exp.notna() & b.isin(list(BORO_ZIPS)) & (exp != b))
    return Alert(mask=m, msg=f"{m.sum()} rows where ZIP prefix implies a different borough", explain=2)


def pair(df, ref):
    c, d = s(df, "complaint_type"), s(df, "descriptor")
    known = c.isin(list(ref.comp_n)).values
    m = np.array([(k and a is not pd.NA and b is not pd.NA and (a, b) not in ref.allow) for k, a, b in zip(known, c, d)], bool)
    return Alert(mask=m, msg=f"{m.sum()} (complaint,descriptor) pairs not in curated allow-list", explain=2)


def resolution(df, ref):
    st, r = s(df, "status"), s(df, "resolution_description").str.lower().fillna("")
    a = st.isin(OPEN_ST) & r.apply(lambda x: any(w in x for w in CLOSED_WORDS))
    b = (st == "Closed") & r.apply(lambda x: any(w in x for w in OPEN_WORDS))
    m = nummask(a | b)
    return Alert(mask=m, msg=f"{m.sum()} rows whose resolution text contradicts status", explain=2)


def pii(df, ref):
    t = (s(df, "resolution_description").fillna("") + " " + s(df, "descriptor").fillna(""))
    m = nummask(t.apply(lambda x: bool(PHONE.search(x) or EMAIL.search(x))))
    return Alert(mask=m, msg=f"{m.sum()} free-text values with phone/email pattern (names undetectable by regex)", explain=2)


DETECTORS = dict(schema=schema, dtype=dtype, datefmt=datefmt, latlon=latlon, dup=dup, neardup=neardup, nullspike=nullspike,
                 closed_before=closed_before, zipboro=zipboro, pair=pair, resolution=resolution, pii=pii)
