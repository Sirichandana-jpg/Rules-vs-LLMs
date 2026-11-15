# DECISION_MATRIX

Project B data source: REAL: NYC 311 Service Requests, created in calendar year 2023 (NYC Open Data erm2-nwe9)

| Proj | Component / check | Choice | Measurement that justifies it | Trade-off |
|---|---|---|---|---|
| A | Free text -> fields (parser) | hybrid | Rule parser 50/50 on dev texts (not held-out); LLM extractor implemented but NOT RUN; both pass one validator | Deterministic/free vs coverage; LLM may extract, never fill gaps |
| A | Missing/ambiguous/contradiction -> clarifying question | rule | 16/16 correct, 0 guesses | Finite checklist; auditable |
| A | Tax computation (both regimes) | rule | 100.0% exact on 277 cases, 100.0% deterministic, p50 1.706 ms, $2.07e-05/1k | Rupee-exact + 100% clause trace; LLM query-time NOT RUN (est. ~886 in-tokens/request) so no accuracy claim |
| A | Law update authoring (Budget) | hybrid (LLM drafts, tests gate) | Compiled-rule runtime matches hand rules on 100.0%; FY change = config keys ['slabs', 'rebate_87a'] | LLM as one-time author, never runtime; stale-FY routing silently wrong in 91/102 cases -> pin FY + golden suites |
| A | Explanation wording | LLM (verbalise trace only) | No measurement run; numbers inserted from the engine trace | Optional; cannot change a number |
| B | Renamed/dropped column | rules | rules: detect 100.0%, FA 0.0%, $0.0/M rows; LLM projected 619,067 tok/M rows (detection NOT RUN) | Rules win on clarity/cost when they tie; statistics win where columns/values are open-ended |
| B | Column type change | rules | rules: detect 100.0%, FA 0.0%, $0.0/M rows; LLM projected 673,533 tok/M rows (detection NOT RUN) | Rules win on clarity/cost when they tie; statistics win where columns/values are open-ended |
| B | Date format switch | rules | rules: detect 100.0%, FA 0.0%, $0.0001/M rows; LLM projected 642,267 tok/M rows (detection NOT RUN) | Rules win on clarity/cost when they tie; statistics win where columns/values are open-ended |
| B | Lat/lon swapped | rules | rules: detect 100.0%, FA 0.0%, $0.0/M rows; LLM projected 2,927,667 tok/M rows (detection NOT RUN) | Rules win on clarity/cost when they tie; statistics win where columns/values are open-ended |
| B | Exact duplicates | rules | rules: detect 100.0%, FA 0.0%, $0.0/M rows; LLM projected 2,977,067 tok/M rows (detection NOT RUN) | Rules win on clarity/cost when they tie; statistics win where columns/values are open-ended |
| B | Near-duplicates | rules (+LLM second opinion on alerts) | rules: detect 100.0%, FA 0.0%, $0.0003/M rows; LLM projected 2,967,400 tok/M rows (detection NOT RUN) | Rules win on clarity/cost when they tie; statistics win where columns/values are open-ended |
| B | Null spike (one agency) | stats | stats: detect 100.0%, FA 0.0%, $0.0001/M rows; LLM projected 2,916,200 tok/M rows (detection NOT RUN) | Rules win on clarity/cost when they tie; statistics win where columns/values are open-ended |
| B | Closed < created | rules | rules: detect 100.0%, FA 0.0%, $0.0003/M rows; LLM projected 2,890,000 tok/M rows (detection NOT RUN) | Rules win on clarity/cost when they tie; statistics win where columns/values are open-ended |
| B | ZIP vs borough | rules (+LLM second opinion on alerts) | rules: detect 100.0%, FA 0.0%, $0.0/M rows; LLM projected 2,968,400 tok/M rows (detection NOT RUN) | Rules win on clarity/cost when they tie; statistics win where columns/values are open-ended |
| B | Complaint vs descriptor | rules (+LLM second opinion on alerts) | rules: detect 100.0%, FA 0.0%, $0.0001/M rows; LLM projected 2,938,600 tok/M rows (detection NOT RUN) | Rules win on clarity/cost when they tie; statistics win where columns/values are open-ended |
| B | Resolution vs status | rules (+LLM second opinion on alerts) | rules: detect 100.0%, FA 0.0%, $0.0001/M rows; LLM projected 2,921,400 tok/M rows (detection NOT RUN) | Rules win on clarity/cost when they tie; statistics win where columns/values are open-ended |
| B | PII in free text | rules (+LLM second opinion on alerts) | rules: detect 100.0%, FA 0.0%, $0.0009/M rows; LLM projected 2,923,867 tok/M rows (detection NOT RUN) | Rules win on clarity/cost when they tie; statistics win where columns/values are open-ended |

Choice values: rule, statistical, LLM, hybrid. Cells marked NOT RUN were never simulated.