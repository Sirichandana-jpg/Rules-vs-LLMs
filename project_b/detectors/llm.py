import json
import numpy as np, pandas as pd
from common import gemini
from ..schema import *
from .base import Alert

HINT = {
    "schema": "Compare the columns/dtypes with the expected schema and report renamed, dropped or extra columns.",
    "dtype": "Report numeric columns (unique_key, latitude, longitude) whose values look like strings.",
    "datefmt": "Report rows whose created_date/closed_date format differs from the dominant ISO format.",
    "latlon": "Report rows where latitude/longitude look swapped or are outside New York City.",
    "dup": "Report rows that are exact duplicates of another row.",
    "neardup": "Report rows that look like the same request as another row with a slightly altered time or text.",
    "nullspike": "Report agencies with an unusually high share of missing values in some column.",
    "closed_before": "Report rows where closed_date is earlier than created_date.",
    "zipboro": "Report rows whose incident_zip cannot belong to the stated borough.",
    "pair": "Report rows whose descriptor is not a sensible descriptor for the complaint_type.",
    "resolution": "Report rows whose resolution_description contradicts the status.",
    "pii": "Report rows whose free text contains personal data (phone numbers, emails, personal names).",
}
STRUCTURAL = {"schema", "dtype", "datefmt"}
SAMPLE = {True: 20, False: 100}          # rows per batch sent to the LLM (structural vs row-level types)
OUT_TOKENS = 150                          # ASSUMPTION for projected output size


def build_prompt(df, ptype, rng=None):
    n = SAMPLE[ptype in STRUCTURAL]
    rng = rng or np.random.default_rng(0)
    smp = df.iloc[np.sort(rng.choice(len(df), min(n, len(df)), replace=False))]
    rows = smp.reset_index().astype(object).where(smp.reset_index().notna(), None).to_dict("records")
    return (f"You review a batch of NYC 311 service-request rows for ONE data-quality problem.\nProblem: {HINT[ptype]}\n"
            f"Expected columns: {COLS}\nBatch dtypes: { {c: str(t) for c, t in df.dtypes.items()} }\nRows (JSON, 'index' = row id):\n"
            f"{json.dumps(rows, default=str)}\nReturn JSON: {{\"problem_present\": bool, \"rows\": [row ids], \"reason\": str}}. Do not guess; if unsure say false.")


def projected_tokens_per_batch(df, ptype):
    return len(build_prompt(df, ptype)) // 4, OUT_TOKENS


def detect(df, ptype, ref=None):
    if not gemini.available():
        return Alert(flag=None, mask=None, msg="NOT RUN (no GEMINI_API_KEY)", explain=-1)
    r = gemini.generate(build_prompt(df, ptype), cache=False)
    d = gemini.parse_json(r["text"])
    m = np.zeros(len(df), bool)
    for i in d.get("rows", []):
        if 0 <= int(i) < len(df): m[int(i)] = True
    return Alert(flag=bool(d.get("problem_present")), mask=m, msg=d.get("reason", ""), explain=2 if m.any() else 1)
