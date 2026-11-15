"""Writes DECISION_MATRIX.md from results_a.json / results_b.json (every justification is a measured number)."""
import json
from pathlib import Path
R = Path(__file__).parent
A = json.loads((R / "project_a/results_a.json").read_text()); B = json.loads((R / "project_b/results_b.json").read_text())
from project_b.injector import NAMES
a, c, p = A["a_hand_rules"], A["c_compiled_rules"], A["parser"]
rows = [
 ("A", "Free text -> fields (parser)", "hybrid", f"Rule parser {p['pass']}/{p['n']} on dev texts (not held-out); LLM extractor implemented but NOT RUN; both pass one validator", "Deterministic/free vs coverage; LLM may extract, never fill gaps"),
 ("A", "Missing/ambiguous/contradiction -> clarifying question", "rule", f"{p['ask_correct']}/{p['ask_cases']} correct, {p['guessed_when_should_ask']} guesses", "Finite checklist; auditable"),
 ("A", "Tax computation (both regimes)", "rule", f"{a['exact_pct']}% exact on {A['n_cases']} cases, {a['deterministic_pct_10x']}% deterministic, p50 {a['latency_ms_p50']} ms, ${a['cpu_usd_per_1000']}/1k", "Rupee-exact + 100% clause trace; LLM query-time NOT RUN (est. ~886 in-tokens/request) so no accuracy claim"),
 ("A", "Law update authoring (Budget)", "hybrid (LLM drafts, tests gate)", f"Compiled-rule runtime matches hand rules on {c['exact_pct']}%; FY change = config keys {A['change']['config_keys_changed']}", "LLM as one-time author, never runtime; stale-FY routing silently wrong in " + f"{a['stale_rules']['silently_wrong_with_stale_rules']}/{a['stale_rules']['fy25_26_cases']} cases -> pin FY + golden suites"),
 ("A", "Explanation wording", "LLM (verbalise trace only)", "No measurement run; numbers inserted from the engine trace", "Optional; cannot change a number"),
]
for pt, nm in NAMES.items():
    t = B["table"][pt]; ch = B["hybrid_choice"][pt]; m = t[ch]
    why = f"{ch}: detect {m['detect_pct']}%, FA {m['false_alarm_pct']}%, ${m['cpu_usd_per_M_rows']}/M rows; LLM projected {t['llm']['tokens_per_M_rows_batch_sampling']:,} tok/M rows (detection NOT RUN)"
    rows.append(("B", nm, ch + (" (+LLM second opinion on alerts)" if pt in ("pair", "resolution", "pii", "zipboro", "neardup") else ""), why, "Rules win on clarity/cost when they tie; statistics win where columns/values are open-ended"))
md = ["# DECISION_MATRIX", "", f"Project B data source: {B['source']}", "", "| Proj | Component / check | Choice | Measurement that justifies it | Trade-off |", "|---|---|---|---|---|"]
md += [f"| {x[0]} | {x[1]} | {x[2]} | {x[3]} | {x[4]} |" for x in rows]
md += ["", "Choice values: rule, statistical, LLM, hybrid. Cells marked NOT RUN were never simulated."]
(R / "DECISION_MATRIX.md").write_text("\n".join(md)); print("DECISION_MATRIX.md written")
