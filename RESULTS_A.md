# RESULTS_A - Income-tax engine: rules vs LLM vs LLM-compiled rules

## 1. Comparison table (Task 4)
| Metric | (a) Hand-coded rules | (b) LLM at query time | (c) LLM-compiled rules |
|---|---|---|---|
| Rupee-exact accuracy (both regimes) | 100.0% (277 cases) | NOT RUN | 100.0% (277 cases) |
| Deterministic over 10 repeats | 100.0% of 60 inputs | NOT RUN | 100.0% of 60 inputs |
| Latency p50 / p95 | 1.706 / 2.724 ms | NOT RUN | 5.518 / 8.512 ms |
| Cost per 1,000 requests | $2.07e-05 (CPU, assumed $0.04/vCPU-h) | NOT RUN; est. 886 in-tokens/request | $6.502e-05 (CPU) |
| Every rupee traces to a clause | 100.0% | NOT RUN | 100.0% |

Trace check = every trace line cites a `[clause]` that exists in the rule text AND the last line equals the reported tax.
Note (b)'s output size (700 tokens) is an assumption when not run. (c) is ~4x slower than (a) in-process because it interprets an AST, still <1 ms.

## 2. Plain-language input (Task 3)
Rule parser: 50/50 gold texts correct; 16/16 ambiguous/incomplete/contradictory texts raised the right
clarifying question; **0** guessed values where a question was required. Caveat: Rule parser was developed against these 50 texts (no held-out set) - expect lower accuracy on unseen phrasing.
`parser.llm_parse` (Gemini extraction + the same validator) is implemented but NOT RUN here. Policy: the LLM may *extract*, never *fill gaps*.

## 3. The law changes (Task 5: FY 2025-26)
| | (a) Hand rules | (b) LLM query-time | (c) Compiled rules |
|---|---|---|---|
| Work needed | new `rules/fy2025_26.json` (keys changed: slabs, rebate_87a); **0 engine lines** | new `rule_text/fy2025_26.md` only | LLM re-compile of the new rule text + human review + diff (`compile_rules.py`); stand-in JSON in repo |
| Time taken | [FILL: your stopwatch minutes] | [FILL] | [FILL] |
| What broke | nothing loud - engine was already data-driven | cannot be known without a run | nothing loud |
| Silent failure if FY not updated | **91/102** FY25-26 cases wrong with NO error | NOT RUN | **91/102** wrong, NO error |
| Unsupported FY | raises KeyError (loud) | n/a | raises KeyError (loud) |

Honest reading: because (a) and (c) were designed with the tax law in data, FY25-26 was a config change, not a code change - **I did not get a "what broke"
story from a genuinely structural change**, and I will not invent one. The measured silent failure is different and real: routing an FY25-26 taxpayer through
FY24-25 rules runs fine and is wrong 91 times out of 102 (new-regime users). Guard: regression tests pinned per FY
+ a release gate that fails if any FY lacks a golden suite. Structural changes (a new deduction, new surcharge rule) would need an engine change in (a), a new DSL function
in (c), and are the case where (b) is most dangerous: it will silently keep applying the old rule text it was not told changed.

## 4. Final design for 100,000 users (Task 6)
| Component | Type | Why (measured) |
|---|---|---|
| Free-text -> structured input | **Hybrid**: rule parser first; LLM extractor only when the rule parser cannot find salary/age; both feed one validator | Rules: 50/50 on dev texts, free, deterministic, but brittle on unseen phrasing. LLM adds coverage; validator guarantees it cannot fill gaps |
| Clarifying questions | **Rule** | Missing/ambiguous/contradictory logic is a finite checklist; 16/16 correct, 0 guesses |
| Tax computation, both regimes | **Rule** (versioned config + small engine), (c) as the Budget-day accelerator | 100.0% exact, 100.0% deterministic, ~1.706 ms, ~$0 per 1,000. Tax must be rupee-exact and reproducible for audit |
| Regime recommendation + explanation text | **Rule** for the numbers; LLM may only *verbalise* the engine's trace | Every rupee has a clause (100%); an LLM narrating the trace cannot change a number if numbers are inserted by template |
| Budget-day rule updates | **LLM-assisted, human-gated**: LLM drafts config/DSL from the new text, tests + differential run against oracle decide | (c) makes the LLM a one-time author, not a runtime dependency |

Keeping it correct through the next Budget: (1) per-FY golden suites (boundaries around every new threshold) generated before code; (2) two independent implementations
(config engine vs compiled DSL) + oracle must agree on 100% of cases or deploy is blocked; (3) pin `fy` explicitly in every request and fail loudly on unknown FY;
(4) verify >=30 cases per FY on the official calculator (template provided); (5) canary: compare production outputs against the oracle nightly on sampled inputs;
(6) never use (b) for the number path - its cost/latency/non-determinism are unacceptable at 100k users and it cannot prove the stale-rule case above is fixed.

