# Rules vs LLMs: when is a deterministic rule right, when does an LLM earn its cost?

Two systems, each built three ways, measured, and defended with evidence.

| | Project A | Project B |
|---|---|---|
| **System** | Income-tax engine for salaried people in India (old vs new regime) | Data-quality layer in front of dashboards (NYC 311 requests, 2023) |
| **Question** | Rules, LLM at query time, or LLM-compiled rules? | Rules, statistics, or LLM review, per problem type? |
| **Answer found** | Rules for the numbers; LLM only as a one-time rule *author* | Cheap rules on every row, statistics per batch, LLM only as a second opinion on already-flagged rows |

---

## 1. What the project does

### Project A: income-tax engine (`project_a/`)
Given a salaried person's details, it computes tax under **both regimes** for FY 2024-25, says which regime is cheaper, and shows **which clause** every rupee came from.

Scope : salary only. Standard deduction, HRA exemption, 80C, 80CCD(1B), 80D (incl. senior-citizen parents),
home-loan interest on a self-occupied house, 87A rebate, surcharge with marginal relief, 4% cess, and the statutory rounding to the nearest Rs 10.

The same calculator is built **three ways**:

| Impl. | File | How it works |
|---|---|---|
| (a) Hand-coded rules | `calc_rules.py` + `rules/*.json` | Small engine; the law (slabs, caps, rebate) lives in versioned JSON. Exact `Fraction` arithmetic. |
| (b) LLM at query time | `calc_llm.py` | Gemini reads the rule text per request and computes the answer. |
| (c) LLM-compiled rules | `calc_compiled.py`, `dsl.py`, `compile_rules.py`, `compiled/*.json` | An LLM converts rule text into a small DSL once; a human reviews it; then it runs with **no LLM**. |

Also in Project A:
- **Test suite** (`tests/`): 277 cases with expected tax for both regimes (boundaries around every threshold, HRA limbs, deduction caps, surcharge edges, seeded random profiles), 12 hand-computed golden cases, and an independent oracle.
- **Plain-language parser** (`parser.py`): turns text (English / Hinglish / incomplete / contradictory) into structured input. It **asks a clarifying question instead of guessing**.
- **FY 2025-26 change experiment**: new-regime slabs and rebate applied to all three designs; silent failures measured.

### Project B: data-quality layer (`project_b/`)
- **Profiler** (`profile.py`): finds real quality problems in the 2023 data, with counts and example keys.
- **Corruption injector** (`injector.py`): injects 12 problem types at a controlled rate (renamed/dropped column, type change, date-format switch, lat/lon swap, exact and near duplicates, null spike in one agency).
- **Three detector families per problem** (`detectors/rules.py`, `stats.py`, `llm.py`): declarative rules, statistical/ML detectors, LLM review.
- **Evaluation** (`evaluate.py`): detection rate, false-alarm rate on clean batches, cost per million rows, throughput, explainability.
- **Hybrid pipeline**: the winner per problem type is picked automatically from the measurements; the LLM is used only on rows already flagged.
- **Scale design**: cost and latency projected for 50M rows/day across 120 customers.

---

## 2. Project structure
```
run_all.py                 one command that reproduces every number
RESULTS_A.md               Project A: comparison table, FY25-26 change log, final design
RESULTS_B.md               Project B: per-problem table, real issues, hybrid pipeline, scale design
DECISION_MATRIX.md         one row per component/check: rule / statistical / LLM / hybrid + the measurement
AI_USAGE.md                which AI tools were used, and one place the AI was wrong
common/gemini.py           small Gemini REST client (no key -> clean "NOT RUN")
project_a/                 calc_rules, calc_llm, calc_compiled, dsl, parser, evaluate, report_a,
                           rules/ (hand-coded law), rule_text/ (text the LLM reads), compiled/ (DSL), tests/
project_b/                 injector, detectors/, evaluate, profile, fetch_311, synth_311, report_b, tests/
make_decision_matrix.py    builds DECISION_MATRIX.md from the measured results
```

---

## 3. How to run

Requires **Python 3.10+** (developed on 3.12). Dependencies: numpy, pandas, scikit-learn, scipy.


```powershell
# Windows (PowerShell)
cd path\to\rules-vs-llms
py -m pip install -r requirements.txt
py run_all.py
```
```bash
# macOS / Linux
cd rules-vs-llms
pip install -r requirements.txt
python run_all.py
```

`run_all.py` runs, in order: test-suite generation, unit tests (golden cases + Project B tests), Project A evaluation and report,
Project B profiling, evaluation and report, and the decision matrix.



---

## 4. results


1. **`RESULTS_A.md`**: the three-way comparison table (accuracy, determinism over 10 repeats, latency, cost per 1,000 requests, clause traceability), parser results, the FY 2025-26 change log, and the final design for 100,000 users.
2. **`RESULTS_B.md`**: real quality problems found, the per-problem detection / false-alarm / cost table for rules vs statistics vs LLM, the hybrid pipeline, and the 50M rows/day scale design.
3. **`DECISION_MATRIX.md`**: every rule-vs-LLM choice tied to a measurement and a stated trade-off.

Raw numbers are in `project_a/results_a.json` and `project_b/results_b.json`.

---

## 5. Key findings

### Project A
| Metric | (a) Hand rules | (b) LLM query-time | (c) Compiled rules |
|---|---|---|---|
| Rupee-exact accuracy (277 cases, both regimes) | **100%** | not evaluated | **100%** |
| Deterministic over 10 repeats | **100%** | not evaluated | **100%** |
| Latency p50 | about 0.17 ms | NOT RUN | about 0.8 ms |
| Every rupee traces to a clause | **100%** | not evaluated | **100%** |
- Plain-language parser: 50/50 gold texts correct; 16/16 ambiguous/incomplete/contradictory texts produced the right clarifying question; 0 guessed values. (Developed against these same 50 texts, so expect lower accuracy on unseen phrasing.)
- **Law change (FY 2025-26):** the two deterministic designs absorbed it as a config change. The measured *silent failure* is routing an FY25-26 taxpayer through FY24-25 rules: it runs without error and is **wrong in 91 of 102 cases**. Fix: pin the FY on every request, fail loudly on an unknown FY, and keep per-FY golden suites as a release gate.

### Project B
- Rules and statistics tie on most problem types. The clear separations: **null spike** (rules only watch fixed columns; the per-agency statistical test sees any column) and **PII** (regex cannot catch personal names).
- Hybrid pipeline end to end: about **42,600 rows/s per core**, about **$0.0003 CPU per million rows**, **0%** false alarms on clean batches.
- Reviewing every row with an LLM once would be about **118M input tokens per million rows**; confirming only alerted rows is about **0.4M**.
- At 50M rows/day the CPU cost is a rounding error; the real cost drivers are false alarms (people) and LLM tokens.

---

## 6. Conclusion
- **Numbers that must be exact and auditable (tax) should be rules.** They were 100% exact, deterministic, traceable and about 0.2 ms at roughly zero cost. An LLM computing tax per request cannot give that guarantee at 100,000 users.
- **An LLM earns its place at the edges, not the core:** drafting rule changes after a Budget (human-reviewed, test-gated), extracting fields from messy text (validated, never allowed to fill gaps), and verbalising an engine's trace.
- **For data quality, layer by cost:** cheap rules on every row, statistics per batch, an LLM only on the small flagged or ambiguous subset (semantic checks such as complaint-vs-descriptor and resolution-vs-status).
- **Silent failures are the real risk.** The most useful safeguards were pinned per-year test suites, two independent implementations that must agree, loud failure on unknown inputs, and cross-checking against an official calculator.

---
