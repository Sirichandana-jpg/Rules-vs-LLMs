import json, time, hashlib, statistics as S, os, sys
from pathlib import Path
from .common import TaxInput, clause_ids, ROOT, error_str
from . import calc_rules, calc_compiled, calc_llm, parser
from .tests.nl_cases import G, check, ASK_KEYS
from common import gemini

CPU_USD_PER_HR = float(os.environ.get("CPU_USD_PER_HR", "0.04"))   
LLM_SUBSET = int(os.environ.get("LLM_CASES", "40"))                 
REPEAT = 10


def cases():
    return json.loads((ROOT / "tests" / "cases.json").read_text())


def exact(res, exp):
    return all(res[r]["total_tax"] == exp[r]["total_tax"] and res[r]["taxable_income"] == exp[r]["taxable_income"] for r in ("old", "new"))


def trace_ok(res, fy):
    ids = clause_ids(fy); items = [t for r in ("old", "new") for t in res[r]["trace"]]
    cited = all(t.get("clause") in ids for t in items)
    last = lambda r: next((t["amount"] for t in reversed(res[r]["trace"]) if "total" in t["item"]), None)
    return bool(items) and cited and all(last(r) == res[r]["total_tax"] for r in ("old", "new"))


def run_impl(name, fn, cs, wrap=lambda c: c):
    errs, wrong, lat, tr, silent_wrong = 0, 0, [], 0, 0
    outs = []
    for c in cs:
        t0 = time.perf_counter()
        try:
            r = fn(TaxInput(**c["input"]))
        except Exception as e:
            errs += 1; outs.append(None); continue
        lat.append((time.perf_counter() - t0) * 1000)
        outs.append(r)
        if not exact(r, c["expected"]): wrong += 1
        tr += trace_ok(r, c["input"]["fy"])
    n = len(cs)
    return {"n": n, "errors": errs, "wrong": wrong, "exact_pct": round(100 * (n - wrong - errs) / n, 2),
            "latency_ms_p50": round(S.median(lat), 3) if lat else None,
            "latency_ms_p95": round(sorted(lat)[int(.95 * len(lat)) - 1], 3) if lat else None,
            "traceable_pct": round(100 * tr / n, 2),
            "cpu_usd_per_1000": round(S.mean(lat) / 1000 / 3600 * CPU_USD_PER_HR * 1000, 8) if lat else None}, outs


def determinism(fn, cs, k=REPEAT):
    """Fraction of inputs whose k repeated runs give byte-identical results."""
    same = 0
    for c in cs:
        hs = {hashlib.sha256(error_str({r: fn(TaxInput(**c["input"]))[r] for r in ("old", "new")}).encode()).hexdigest() for _ in range(k)}
        same += len(hs) == 1
    return round(100 * same / len(cs), 2)


def stale_experiment(fn_name, fn, cs):
    """Task 5: what if someone forgets to update? FY25-26 inputs forced through FY24-25 law -> silent wrong answers?"""
    cs = [c for c in cs if c["input"]["fy"] == "2025-26"]; wrong = loud = 0
    for c in cs:
        d = dict(c["input"], fy="2024-25")
        try: r = fn(TaxInput(**d))
        except Exception: loud += 1; continue
        wrong += not exact(r, c["expected"])
    return {"fy25_26_cases": len(cs), "silently_wrong_with_stale_rules": wrong, "raised_error": loud}


def main():
    cs = cases(); out = {"n_cases": len(cs), "assumptions": {"cpu_usd_per_hr": CPU_USD_PER_HR}}
    for name, fn in (("a_hand_rules", calc_rules.calculate), ("c_compiled_rules", calc_compiled.calculate)):
        m, _ = run_impl(name, fn, cs); m["deterministic_pct_10x"] = determinism(fn, cs[:60]); out[name] = m
        m["stale_rules"] = stale_experiment(name, fn, cs)
        try:
            fn(TaxInput(fy="2026-27", gross_salary=1)); m["unsupported_fy"] = "NO ERROR (silent!)"
        except KeyError: m["unsupported_fy"] = "raises KeyError (loud)"
    # (b)
    sub = cs[::max(1, len(cs) // LLM_SUBSET)][:LLM_SUBSET]
    if gemini.available():
        m, outs = run_impl("b_llm_query_time", calc_llm.calculate, sub)
        use = [o["_usage"] for o in outs if o]
        m["determinism_pct_10x_on_5_inputs"] = determinism(lambda i: calc_llm.calculate(i), sub[:5])
        m["avg_in_tokens"] = S.mean(u["in"] for u in use); m["avg_out_tokens"] = S.mean(u["out"] for u in use)
        m["latency_s_p50"] = S.median(u["latency_s"] for u in use); m["n_subset"] = len(sub)
        pr = gemini.price_per_m()
        m["usd_per_1000"] = round((m["avg_in_tokens"] * pr[0] + m["avg_out_tokens"] * pr[1]) / 1e6 * 1000, 4) if pr else "set GEMINI_PRICE_*_PER_M"
        out["b_llm_query_time"] = m
    else:
        tin = S.mean(calc_llm.estimate_tokens(TaxInput(**c["input"]))[0] for c in sub)
        out["b_llm_query_time"] = {"status": "NOT RUN (no GEMINI_API_KEY in this environment)", "est_in_tokens_per_request": round(tin),
                                   "est_out_tokens_per_request": 700, "note": "estimates are chars/4 of the real prompt; output size is an assumption"}
    # parser (Task 3)
    res = [(t, g, parser.parse(t)) for t, g in G]
    ok = [check(t, g, r) for t, g, r in res]
    ask_cases = [x for x in res if "ask" in x[1]]
    out["parser"] = {"n": len(G), "pass": sum(ok), "ask_cases": len(ask_cases),
                     "ask_correct": sum(check(*x) for x in ask_cases),
                     "guessed_when_should_ask": sum(any(ASK_KEYS[a] in r["input"] for a in g["ask"]) for _, g, r in ask_cases),
                     "note": "Rule parser was developed against these 50 texts (no held-out set) - expect lower accuracy on unseen phrasing."}
    # change analysis (Task 5)
    f24, f25 = (json.loads((ROOT / "rules" / f"fy{y}.json").read_text()) for y in ("2024_25", "2025_26"))
    diff = [k for k in f24 if f24[k] != f25[k] and k not in ("fy", "source")]
    sha = lambda p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:12]
    out["change"] = {"config_keys_changed": diff, "engine_sha256": {p: sha(p) for p in ("calc_rules.py", "dsl.py", "calc_compiled.py")}}
    (ROOT / "results_a.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
