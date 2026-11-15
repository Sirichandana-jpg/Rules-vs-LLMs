import numpy as np, pandas as pd
from .schema import *


def synth(n=300_000, seed=0):
    rng = np.random.default_rng(seed)
    ag = rng.choice(list(AGENCY_W), n, p=np.array(list(AGENCY_W.values())) / sum(AGENCY_W.values()))
    ct, ds = np.empty(n, object), np.empty(n, object)
    for a, cm in AGENCY_COMPLAINTS.items():
        idx = np.where(ag == a)[0]; types = list(cm)
        t = rng.choice(len(types), len(idx), p=np.arange(len(types), 0, -1) / np.arange(len(types), 0, -1).sum())
        for j, tn in enumerate(types):
            sel = idx[t == j]; ct[sel] = tn; ds[sel] = rng.choice(cm[tn], len(sel))
    bo = rng.choice(list(BORO_ZIPS), n, p=[.2, .17, .3, .27, .06])
    zp, la, lo = np.empty(n, object), np.empty(n), np.empty(n)
    for b, zl in BORO_ZIPS.items():
        i = np.where(bo == b)[0]; zp[i] = rng.choice(zl, len(i)); bx = BORO_BOX[b]
        la[i] = rng.uniform(bx[0], bx[1], len(i)); lo[i] = rng.uniform(bx[2], bx[3], len(i))
    sec = np.sort(rng.integers(0, 365 * 86400, n))
    created = pd.Timestamp("2023-01-01") + pd.to_timedelta(sec, "s")
    status = rng.choice(["Closed", "Open", "In Progress", "Pending"], n, p=[.86, .06, .05, .03])
    lag = pd.to_timedelta(np.exp(rng.normal(3.2, 1.3, n)) * 3600, "s")
    closed = pd.Series(created + lag).where(status == "Closed")
    res = np.empty(n, object)
    for i in range(n):
        res[i] = (CLOSED_RES if status[i] == "Closed" else OPEN_RES)[rng.integers(0, len(CLOSED_RES) if status[i] == "Closed" else len(OPEN_RES))].format(a=ag[i])
    addr = np.array([f"{a} {s} {t}" for a, s, t in zip(rng.integers(1, 999, n), rng.choice(["MAIN", "BROADWAY", "OAK", "PARK", "5TH", "MAPLE", "LEXINGTON"], n), rng.choice(["ST", "AVE", "BLVD"], n))], object)
    df = pd.DataFrame({"unique_key": 55_000_000 + np.arange(n), "created_date": created.strftime(ISO_FMT), "closed_date": closed.dt.strftime(ISO_FMT),
                       "agency": ag, "complaint_type": ct, "descriptor": ds, "incident_zip": zp, "incident_address": addr, "borough": bo,
                       "city": np.where(bo == "STATEN ISLAND", "STATEN ISLAND", bo.astype(str)), "status": status, "resolution_description": res,
                       "latitude": la, "longitude": lo})
    # natural defects (so rules/stats have a realistic false-alarm floor)
    m = lambda p: rng.random(n) < p
    df.loc[m(.004), "incident_zip"] = np.nan
    df.loc[m(.01), ["latitude", "longitude"]] = np.nan
    k = m(.002); df.loc[k, "incident_zip"] = [BORO_ZIPS["BRONX"][0]] * k.sum()
    k = m(.0005) & df.closed_date.notna(); df.loc[k, "closed_date"] = df.loc[k, "created_date"]
    k = m(.0005) & df.closed_date.notna()
    df.loc[k, "closed_date"] = (pd.to_datetime(df.loc[k, "created_date"]) - pd.Timedelta(hours=2)).dt.strftime(ISO_FMT)
    df.loc[m(.003), "borough"] = "Unspecified"
    return df[COLS].reset_index(drop=True)
