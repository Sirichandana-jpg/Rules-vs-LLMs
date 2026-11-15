import json, os, time, math
from pathlib import Path
import numpy as np, pandas as pd
from .data import load_pool, batches
from .injector import inject, PTYPES
from .detectors import rules, stats, llm
from .detectors.base import Reference
from common import gemini

SEED, BATCH, RATE = 0, 5000, 0.05
N_CAL, N_CLEAN, N_BAD, N_MIX = 10, 30, 20, 40
CPU_USD_PER_HR = float(os.environ.get("CPU_USD_PER_HR", "0.04"))   # ASSUMPTION (1 vCPU-hour); override via env
FAMS = {"rules": rules.DETECTORS, "stats": stats.DETECTORS}
SEMANTIC = {"pair", "resolution", "pii", "zipboro", "neardup"}
OUT = Path(__file__).parent / "results_b.json"


def decide(a, thr):
    if a.flag is not None: return bool(a.flag)
    return a.mask is not None and int(a.mask.sum()) > thr


def calibrate(det, cal, ref):
    """Alert threshold = baseline count on clean calibration batches: ceil(mean + 4*std) + 2. Zero-tolerance for explicit-flag checks."""
    c = [int(det(b, ref).mask.sum()) if det(b, ref).mask is not None else 0 for b in cal]
    return math.ceil(np.mean(c) + 4 * np.std(c)) + 2


def timed(det, b, ref):
    t = time.perf_counter(); a = det(b, ref); return a, time.perf_counter() - t


def main():
    rng = np.random.default_rng(SEED)
    pool, source = load_pool()
    perm = rng.permutation(len(pool)); n_ref = min(60000, len(pool) // 4)
    ref = Reference().fit(pool.iloc[perm[:n_ref]].reset_index(drop=True))
    rest = pool.iloc[perm[n_ref:]].reset_index(drop=True)
    cal = list(batches(rest, N_CAL, BATCH, rng)); clean = list(batches(rest, N_CLEAN, BATCH, rng))
    res = {"source": source, "batch_rows": BATCH, "inject_rate": RATE, "n_clean": N_CLEAN, "n_corrupt_per_type": N_BAD,
           "cpu_usd_per_hr_assumed": CPU_USD_PER_HR, "table": {}, "thr": {}}
    for p in PTYPES:
        bad = [inject(b, p, RATE, rng) for b in batches(rest, N_BAD, BATCH, rng)]
        res["table"][p] = {}
        for fam, D in FAMS.items():
            det = D[p]; thr = calibrate(det, cal, ref); res["thr"][f"{fam}/{p}"] = thr
            tt = rows = 0; fp = 0; fpr = []; ex = 0
            for b in clean:
                a, dt = timed(det, b, ref); tt += dt; rows += len(b); fp += decide(a, thr)
                if a.mask is not None: fpr.append(a.mask.mean())
            hit = 0; rec = []
            for bc, truth in bad:
                a, dt = timed(det, bc, ref); tt += dt; rows += len(bc); hit += decide(a, thr); ex = max(ex, a.explain)
                if a.mask is not None and truth["rows"] is not None and len(a.mask) == len(truth["rows"]):
                    rec.append((a.mask & truth["rows"]).sum() / truth["rows"].sum())
            rps = rows / tt
            res["table"][p][fam] = {"detect_pct": round(100 * hit / N_BAD, 1), "false_alarm_pct": round(100 * fp / N_CLEAN, 1),
                                    "row_recall_pct": round(100 * np.mean(rec), 1) if rec else None,
                                    "row_fpr_pct": round(100 * np.mean(fpr), 3) if fpr else None, "rows_per_s": round(rps),
                                    "cpu_usd_per_M_rows": round(1e6 / rps / 3600 * CPU_USD_PER_HR, 4), "explain_0_2": ex, "alert_threshold_rows": thr}
        # LLM family: projected volume (always), detection only if a key exists
        tok = np.mean([sum(llm.projected_tokens_per_batch(bc, p)) for bc, _ in bad[:3]])
        e = {"status": "NOT RUN (no GEMINI_API_KEY)" if not gemini.available() else "run", "tokens_per_batch_projected": round(tok),
             "tokens_per_M_rows_batch_sampling": round(tok / BATCH * 1e6)}
        if gemini.available():
            n_llm = int(os.environ.get("LLM_BATCHES", "5")); hit = sum(bool(llm.detect(bc, p).flag) for bc, _ in bad[:n_llm])
            fa = sum(bool(llm.detect(b, p).flag) for b in clean[:n_llm])
            e.update({"detect_pct": round(100 * hit / n_llm, 1), "false_alarm_pct": round(100 * fa / n_llm, 1), "n_batches": n_llm})
        res["table"][p]["llm"] = e
    # full per-row LLM review cost projection (every row, ~avg row tokens)
    row_tok = np.mean([len(json.dumps(r, default=str)) for r in rest.sample(500, random_state=0).to_dict("records")]) / 4
    res["llm_full_per_row_tokens_per_M_rows_per_check"] = round(row_tok * 1e6)
    res["llm_row_tokens"] = round(float(row_tok))
    # ---- hybrid: pick winner per type among rules/stats (score = detect - 2*false_alarm; ties -> rules = cheaper/clearer)
    choice = {}
    for p in PTYPES:
        sc = {f: res["table"][p][f]["detect_pct"] - 2 * res["table"][p][f]["false_alarm_pct"] for f in FAMS}
        choice[p] = "stats" if sc["stats"] > sc["rules"] + 1e-9 else "rules"
    res["hybrid_choice"] = choice
    res["hybrid"] = run_hybrid(rest, ref, choice, res["thr"], clean, rng)
    OUT.write_text(json.dumps(res, indent=1, default=str)); print("wrote", OUT, "|", source)


def hybrid_batch(df, ref, choice, thr):
    """rules/stats per type -> alerts. Schema/dtype failures quarantine the batch (other detectors assume a valid schema).
    Stage 3 (LLM) would only confirm/explain rows of ALERTED semantic checks: we return the prompt size it would send."""
    t0 = time.perf_counter(); alerts = {}; llm_chars = 0
    for p in ("schema", "dtype"):
        alerts[p] = decide(FAMS[choice[p]][p](df, ref), thr[f"{choice[p]}/{p}"])
    if not any(alerts.values()):
        for p in PTYPES:
            if p in alerts: continue
            a = FAMS[choice[p]][p](df, ref); alerts[p] = decide(a, thr[f"{choice[p]}/{p}"])
            if alerts[p] and p in SEMANTIC and a.mask is not None:
                sub = df[a.mask].head(30); llm_chars += len(sub.to_json(orient="records")) + 400
    return alerts, time.perf_counter() - t0, llm_chars // 4


def run_hybrid(rest, ref, choice, thr, clean, rng):
    rowtypes = [p for p in PTYPES if p not in ("schema", "dtype")]
    fa = {p: 0 for p in PTYPES}; any_fa = 0; T = 0; R = 0; tok = 0
    for b in clean:
        al, dt, tk = hybrid_batch(b, ref, choice, thr); T += dt; R += len(b); tok += tk
        any_fa += any(al.values())
        for p, v in al.items(): fa[p] += v
    det = {p: [0, 0] for p in PTYPES}
    mix = []
    for i, b in enumerate(batches(rest, N_MIX, BATCH, rng)):
        k = int(rng.integers(1, 4)); chosen = list(rng.choice(rowtypes, k, replace=False)); cur = b
        for p in chosen: cur, _ = inject(cur, p, RATE, rng)
        mix.append((cur, chosen))
    for i, p in enumerate(("schema", "dtype")):
        for b in batches(rest, 10, BATCH, rng): mix.append((inject(b, p, RATE, rng)[0], [p]))
    for cur, chosen in mix:
        al, dt, tk = hybrid_batch(cur, ref, choice, thr); T += dt; R += len(cur); tok += tk
        for p in chosen:
            det[p][1] += 1; det[p][0] += al[p] if p in al else 0
    return {"per_type_detect_pct": {p: round(100 * h / n, 1) if n else None for p, (h, n) in det.items()},
            "per_type_detect_n": {p: n for p, (h, n) in det.items()},
            "per_type_false_alarm_pct_on_clean": {p: round(100 * v / len(clean), 1) for p, v in fa.items()},
            "any_alert_on_clean_batch_pct": round(100 * any_fa / len(clean), 1),
            "rows_per_s": round(R / T), "cpu_usd_per_M_rows": round(1e6 / (R / T) / 3600 * CPU_USD_PER_HR, 4),
            "llm_confirm_tokens_per_M_rows_projected": round(tok / R * 1e6), "n_mixed_batches": len(mix),
            "note": "mixed batches have 1-3 simultaneous row-level corruptions; schema/dtype batches tested alone. LLM stage NOT RUN: tokens are what it would receive."}


if __name__ == "__main__":
    main()
