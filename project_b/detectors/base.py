from dataclasses import dataclass
import numpy as np, pandas as pd
from ..schema import *


@dataclass
class Alert:
    flag: object = None            # explicit batch decision; None => decide by calibrated count of mask rows
    mask: object = None            # bool array over rows flagged (None for batch-level-only checks)
    msg: str = ""
    explain: int = 1               # rubric: 0 = score only, 1 = batch-level metric/column named, 2 = row ids + observed vs expected value


def s(df, c):
    return df[c].astype("string") if c in df else pd.Series([pd.NA] * len(df), dtype="string")


def ts(df, c):
    return pd.to_datetime(s(df, c), format=ISO_FMT, errors="coerce")


def nummask(x):
    return np.asarray(x.fillna(False), dtype=bool)


class Reference:
    """Statistics learned once from CLEAN reference batches (used by the statistical detectors and the pair allow-list)."""

    def fit(self, ref):
        self.cols = list(ref.columns)
        z, b = s(ref, "incident_zip"), s(ref, "borough")
        g = pd.DataFrame({"z": z, "b": b}).dropna().groupby("z")["b"].agg(lambda x: (x.value_counts().index[0], x.value_counts().iloc[0] / len(x), len(x)))
        self.zip_boro = {k: v[0] for k, v in g.items() if v[2] >= 20 and v[1] >= .95}
        pc = pd.DataFrame({"c": s(ref, "complaint_type"), "d": s(ref, "descriptor")}).dropna()
        self.pair_n = pc.groupby(["c", "d"]).size().to_dict(); self.comp_n = pc.groupby("c").size().to_dict()
        self.V = pc["d"].nunique(); self.allow = {k for k, v in self.pair_n.items() if v >= 5}
        self.null_p = {}
        for a, g2 in ref.groupby("agency"):
            self.null_p[a] = g2.isna().mean().to_dict()
        self.null_global = ref.isna().mean().to_dict()
        for c in ("latitude", "longitude"):
            v = pd.to_numeric(ref[c], errors="coerce").dropna()
            m = float(v.median()); self.__dict__[c + "_med"] = m; self.__dict__[c + "_mad"] = float((v - m).abs().median() * 1.4826) or 1e-6
        sh = s(ref, "created_date").dropna().map(shape).value_counts(normalize=True)
        self.shapes = set(sh[sh >= .001].index)
        tpl = pd.DataFrame({"t": s(ref, "resolution_description").map(template), "st": s(ref, "status")}).dropna()
        g = tpl.groupby("t")["st"].agg(lambda x: (x.value_counts().index[0], x.value_counts().iloc[0] / len(x), len(x)))
        self.tpl_status = {k: v[0] for k, v in g.items() if v[2] >= 20 and v[1] >= .95}
        d = (ts(ref, "closed_date") - ts(ref, "created_date")).dt.total_seconds() / 3600
        self.dur = {}
        for a, idx in ref.groupby("agency").groups.items():
            x = np.arcsinh(d.loc[idx].dropna())
            if len(x) > 30: self.dur[a] = (float(x.median()), float((x - x.median()).abs().median() * 1.4826) or 1e-6)
        return self


def shape(x):
    import re
    return re.sub(r"[A-Za-z]", "a", re.sub(r"\d", "9", x))


def template(x):
    import re
    return re.sub(r"\d+", "#", str(x).lower())[:50]
