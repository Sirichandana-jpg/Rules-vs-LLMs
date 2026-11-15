"""Family (b): statistical / learned detectors, fitted on clean reference batches (base.Reference)."""
import re, difflib
import numpy as np, pandas as pd
from .base import *


def schema(df, ref):
    a, b = set(ref.cols), set(df.columns); j = len(a & b) / len(a | b)
    return Alert(flag=j < 1, msg=f"column-set Jaccard vs reference = {j:.3f} (statistics add nothing over a set comparison here)", explain=1)


def dtype(df, ref):
    bad = []
    for c in NUMERIC_COLS:
        if c in df:
            rate = pd.to_numeric(df[c], errors="coerce").notna().mean()
            if not pd.api.types.is_numeric_dtype(df[c]) and rate > .5: bad.append(c)
    return Alert(flag=bool(bad), msg=f"{bad}: numeric-looking values stored as text", explain=1)


def datefmt(df, ref):
    sh = s(df, "created_date").map(lambda x: shape(x) if isinstance(x, str) else None)
    m = nummask(sh.notna() & ~sh.isin(ref.shapes))
    return Alert(mask=m, msg=f"{m.sum()} values with a character-shape never seen in reference", explain=2)


def latlon(df, ref):
    la, lo = pd.to_numeric(df.get("latitude"), errors="coerce"), pd.to_numeric(df.get("longitude"), errors="coerce")
    z = ((la - ref.latitude_med) / ref.latitude_mad).abs().gt(8) | ((lo - ref.longitude_med) / ref.longitude_mad).abs().gt(8)
    m = nummask(z)
    return Alert(mask=m, msg=f"{m.sum()} coordinates >8 robust-sigma from the reference centre", explain=2)


def dup(df, ref):
    h = pd.util.hash_pandas_object(df.astype(str), index=False)
    m = h.duplicated(keep="first").values
    return Alert(mask=m, msg=f"{m.sum()} rows with a row-hash seen earlier", explain=2)


def neardup(df, ref):
    t = ts(df, "created_date")
    o = pd.DataFrame({"a": s(df, "agency"), "z": s(df, "incident_zip"), "t": t,
                      "x": (s(df, "complaint_type").fillna("") + s(df, "descriptor").fillna("") + s(df, "incident_address").fillna("")).str.lower().str.strip()}).reset_index()
    o = o.sort_values(["a", "z", "t"]); m = np.zeros(len(df), bool)
    prev = o.groupby(["a", "z"], sort=False).shift(1)
    cand = ((o["t"] - prev["t"]).dt.total_seconds() < 300).fillna(False).values
    for i in np.where(cand)[0]:
        if difflib.SequenceMatcher(None, o["x"].iloc[i], prev["x"].iloc[i]).ratio() >= .85: m[o["index"].iloc[i]] = True
    return Alert(mask=m, msg=f"{m.sum()} rows within 5 min and >=0.85 text similarity of an earlier row in same agency+zip", explain=2)


def nullspike(df, ref):
    hit = []; m = np.zeros(len(df), bool)
    for a, g in df.groupby("agency"):
        if len(g) < 30 or a not in ref.null_p: continue
        rate = g.isna().mean()
        for c in rate.index:
            p0 = max(ref.null_p[a].get(c, 0), .005); z = (rate[c] - p0) / np.sqrt(p0 * (1 - p0) / len(g))
            if z > 6 and rate[c] - p0 > .2:
                hit.append((a, c, round(rate[c], 2), round(p0, 3))); m[np.where((df.agency == a).values & df[c].isna().values)[0]] = True
    return Alert(flag=bool(hit), mask=m, msg=f"null-rate spike (agency, column, observed, baseline): {hit[:3]}", explain=2)


def closed_before(df, ref):
    d = (ts(df, "closed_date") - ts(df, "created_date")).dt.total_seconds() / 3600
    z = pd.Series(0.0, index=df.index)
    for a, (med, mad) in ref.dur.items():
        i = (df.agency == a).values; z[i] = (np.arcsinh(d[i]) - med) / mad
    m = nummask((d < 0) | (z.abs() > 6))
    return Alert(mask=m, msg=f"{m.sum()} durations negative or >6 robust-sigma from the agency's norm", explain=2)


def zipboro(df, ref):
    exp = s(df, "incident_zip").map(ref.zip_boro); b = s(df, "borough")
    m = nummask(exp.notna() & b.notna() & (exp != b))
    return Alert(mask=m, msg=f"{m.sum()} rows whose borough disagrees with the learned majority borough of their ZIP", explain=2)


def pair(df, ref, alpha=.01):
    out = []
    for c, d in zip(s(df, "complaint_type"), s(df, "descriptor")):
        if c is pd.NA or d is pd.NA or c not in ref.comp_n: out.append(False); continue
        p = (ref.pair_n.get((c, d), 0) + alpha) / (ref.comp_n[c] + alpha * ref.V); out.append(p < 1e-3)
    m = np.array(out, bool)
    return Alert(mask=m, msg=f"{m.sum()} rows with P(descriptor | complaint) < 0.001 (smoothed)", explain=2)


def resolution(df, ref):
    t = s(df, "resolution_description").map(lambda x: template(x) if isinstance(x, str) else None)
    exp = t.map(ref.tpl_status); m = nummask(exp.notna() & (exp != s(df, "status")))
    return Alert(mask=m, msg=f"{m.sum()} rows whose status differs from the status that text template almost always has", explain=2)


def pii(df, ref):
    def f(x):
        if not isinstance(x, str): return False
        words = re.findall(r"[A-Za-z']+", x)
        names = any(a[:1].isupper() and a[1:].islower() and b[:1].isupper() and b[1:].islower() and i > 0 for i, (a, b) in enumerate(zip(words, words[1:])))
        return "@" in x or sum(ch.isdigit() for ch in x) >= 10 or names
    m = nummask(s(df, "resolution_description").map(f))
    return Alert(mask=m, msg=f"{m.sum()} text values with '@', >=10 digits, or consecutive Title-case words (name-like)", explain=1)


DETECTORS = dict(schema=schema, dtype=dtype, datefmt=datefmt, latlon=latlon, dup=dup, neardup=neardup, nullspike=nullspike,
                 closed_before=closed_before, zipboro=zipboro, pair=pair, resolution=resolution, pii=pii)
