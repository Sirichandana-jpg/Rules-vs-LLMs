
# RESULTS_A — Income-Tax Engine: Rules vs. LLM vs. LLM-Compiled Rules

## 1. Comparison Table (Task 4)

| Metric | (a) Hand-Coded Rules | (b) LLM at Query Time | (c) LLM-Compiled Rules |
|---|---:|---:|---:|
| Rupee-exact accuracy (both regimes) | 100.0% (277 cases) | NOT RUN | 100.0% (277 cases) |
| Deterministic over 10 repeats | 100.0% of 60 inputs | NOT RUN | 100.0% of 60 inputs |
| Latency (p50 / p95) | 1.706 / 2.724 ms | NOT RUN | 5.518 / 8.512 ms |
| Cost per 1,000 requests | $2.07e-05 (CPU, assumed $0.04/vCPU-hour) | NOT RUN; estimated 886 input tokens/request | $6.502e-05 (CPU) |
| Every rupee traces to a clause | 100.0% | NOT RUN | 100.0% |

**Trace verification:** Every trace line references a `[clause]` present in the rule text, and the final trace line matches the reported tax amount.

**Note:** The output size for approach (b), estimated at 700 tokens, is an assumption because the approach was not executed. Approach (c) is approximately 4× slower than approach (a) in-process because it interprets an AST, although its measured latency remains below 1 ms.

---

## 2. Plain-Language Input (Task 3)

The rule-based parser achieved the following results:

- **50/50** gold-standard inputs parsed correctly.
- **16/16** ambiguous, incomplete, or contradictory inputs triggered the appropriate clarifying question.
- **0** values were guessed when clarification was required.

**Limitation:** The rule-based parser was developed and evaluated against these 50 inputs. No held-out test set was used, so its accuracy on unseen phrasing may be lower.

`parser.llm_parse` (Gemini extraction followed by the same validator) is implemented but **NOT RUN**.

**Design principle:** The LLM may extract information, but it must never fill missing or ambiguous values.

---

## 3. When the Tax Law Changes (Task 5: FY 2025–26)

| Evaluation | (a) Hand-Coded Rules | (b) LLM at Query Time | (c) LLM-Compiled Rules |
|---|---|---|---|
| Work required | Add `rules/fy2025_26.json` (changed keys: `slabs`, `rebate_87a`); 0 engine lines changed | Update `rule_text/fy2025_26.md` only | Recompile the new rule text using the LLM, followed by human review and a diff using `compile_rules.py`; stand-in JSON included in the repository |
| Time taken | ~5 mins | ~10 mins | ~20 mins |
| What broke? | Nothing obvious; the engine was already data-driven | Cannot be determined without execution | Nothing obvious |
| Silent failure if FY is not updated | 91/102 FY 2025–26 cases wrong, with no error | NOT RUN | 91/102 cases wrong, with no error |
| Unsupported FY | Raises `KeyError` (fails loudly) | N/A | Raises `KeyError` (fails loudly) |

### Analysis

Approaches (a) and (c) were designed to represent tax law as data. Therefore, supporting FY 2025–26 required a configuration change rather than an engine-code change.

I did not observe a genuine structural-change failure in these approaches, and I will not invent one.

The measured silent failure is different and real: routing an FY 2025–26 taxpayer through FY 2024–25 rules completes without an error but produces incorrect results in **91 out of 102 cases (new-regime users)**.

**Safeguard:** Maintain regression tests pinned to each financial year and introduce a release gate that fails if any financial year lacks a golden test suite.

A genuinely structural change, such as introducing a new deduction or surcharge rule, would require:

- An engine modification in approach (a).
- A new DSL function in approach (c).
- Updated rule text in approach (b).

This is where approach (b) becomes particularly risky: it may silently continue applying outdated rule text if it is not informed of the change.

---

## 4. Final Design for 100,000 Users (Task 6)

| Component | Selected Approach | Evidence and Rationale |
|---|---|---|
| Free-text to structured input | **Hybrid:** Rule parser first; LLM extractor only when the rule parser cannot identify salary or age. Both feed into one validator. | The rule parser achieved 50/50 on development inputs. It is deterministic and free to execute, but may be brittle on unseen phrasing. The LLM can improve coverage, while the validator prevents it from filling missing values. |
| Clarifying questions | **Rules** | Missing, ambiguous, and contradictory inputs can be handled through a finite checklist. The parser handled 16/16 cases correctly with zero unsupported guesses. |
| Tax computation (both regimes) | **Rules:** Versioned configuration and a small calculation engine. Approach (c) serves as a Budget-day accelerator. | Both deterministic approaches achieved 100% rupee-exact accuracy and 100% determinism in the evaluated cases. Approach (a) recorded a p50 latency of 1.706 ms. Tax calculations must be exact and reproducible for auditing. |
| Regime recommendation and explanation | **Rules for numerical results; LLM only to verbalise the engine's trace.** | Every rupee is linked to a rule clause in the evaluated deterministic approaches. The LLM may explain the trace, but numerical values must come directly from the engine. |
| Budget-day rule updates | **LLM-assisted, human-gated.** The LLM drafts configuration or DSL changes from updated rule text, followed by testing and differential comparison against the oracle. | Approach (c) makes the LLM a one-time authoring assistant rather than a runtime dependency. |

### Keeping the System Correct Through the Next Budget

1. **Financial-year-specific testing:** Create a golden test suite for every financial year, including boundary cases around every new threshold, before modifying the implementation.

2. **Independent verification:** Run two independent implementations (configuration-based engine and compiled DSL) against the oracle. Block deployment unless all evaluated cases agree.

3. **Explicit financial-year handling:** Require an explicit FY value in every request and fail loudly when an unsupported FY is provided.

4. **Official calculator verification:** Verify at least 30 cases per financial year against the official calculator using the verification template provided in the repository.

5. **Production monitoring:** Run nightly canary checks comparing sampled production outputs against the oracle.

6. **Avoid LLM-based numerical computation:** Never use approach (b) for the numeric calculation path. Its cost, latency, and non-determinism make it unsuitable for rupee-exact calculations at 100,000-user scale. It also cannot independently guarantee that stale-rule failures have been corrected.
7. 
