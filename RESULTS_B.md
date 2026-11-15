# RESULTS_B - Data-quality layer for NYC 311 (rules vs statistics vs LLM)

**Data source of every number below:** REAL: NYC 311 Service Requests, created in calendar year 2023 (NYC Open Data erm2-nwe9)


## 1. Real quality problems already in the data (Task 1)

Profiled 219,000 rows (REAL: NYC 311 Service Requests, created ...). Full list: `project_b/profile_b.json`.

| Problem | Rows | % | Example unique_keys |
|---|---|---|---|
| closed_date earlier than created_date | 204 | 0.093% | 56454589, 56454607, 56477303 |
| closed_date equals created_date (zero-length) | 2,941 | 1.343% | 56412696, 56412810, 56413014 |
| status=Closed but closed_date null | 1,210 | 0.553% | 57896350, 57944220, 57962855 |
| closed_date present but status not Closed | 231 | 0.105% | 56435292, 56435352, 56454062 |
| latitude/longitude missing | 2,726 | 1.245% | 56408061, 56412433, 56412512 |
| incident_zip missing | 2,381 | 1.087% | 56408061, 56412433, 56412512 |
| ZIP prefix implies different borough | 51 | 0.023% | 56453999, 56487199, 56540638 |
| borough = 'UNSPECIFIED'/missing | 198 | 0.09% | 56419618, 56419743, 56419755 |
| Phone/email pattern in free text | 5,471 | 2.498% | 56412539, 56412602, 56412618 |
| complaint_type: same value in different case/whitespace | 977 | 0.446% | 56412498, 56412539, 56412618 |
| descriptor: same value in different case/whitespace | 143 | 0.065% | 56412496, 56419789, 56435239 |

## 2. Per-problem detection, false alarms, cost (Tasks 3-4)

Detect = % of corrupted batches alerted; FA = % of clean batches alerted; Rec = row-level recall; k rows/s measured in-process on this machine (batch-level schema checks are constant-time, shown capped); $/M = CPU dollars per million rows; Expl = explainability rubric 0-2 (2 = row evidence + expected value, 1 = batch-level metric, 0 = score only).

| Problem | Rules: Detect/FA/Rec | Rules k rows/s, $/M, Expl | Stats: Detect/FA/Rec | Stats k rows/s, $/M, Expl | LLM (Gemini) | LLM projected tokens/M rows (sampled review) |
|---|---|---|---|---|---|---|
| Renamed/dropped column | 100.0/0.0/- | 83808, 0.0, 2 | 100.0/0.0/- | 99999, 0.0, 1 | NOT RUN | 619,067 |
| Column type change | 100.0/0.0/- | 17138, 0.0, 2 | 100.0/0.0/- | 890, 0.0, 1 | NOT RUN | 673,533 |
| Date format switch | 100.0/0.0/100.0 | 140, 0.0001, 2 | 100.0/0.0/100.0 | 55, 0.0002, 2 | NOT RUN | 642,267 |
| Lat/lon swapped | 100.0/0.0/100.0 | 5214, 0.0, 2 | 100.0/0.0/100.0 | 5804, 0.0, 2 | NOT RUN | 2,927,667 |
| Exact duplicates | 100.0/0.0/100.0 | 458, 0.0, 2 | 100.0/0.0/100.0 | 37, 0.0003, 2 | NOT RUN | 2,977,067 |
| Near-duplicates | 100.0/0.0/100.0 | 32, 0.0003, 2 | 100.0/0.0/98.8 | 28, 0.0004, 2 | NOT RUN | 2,967,400 |
| Null spike (one agency) | 35.0/0.0/35.0 | 1033, 0.0, 2 | 100.0/0.0/100.0 | 100, 0.0001, 2 | NOT RUN | 2,916,200 |
| Closed < created | 100.0/0.0/100.0 | 39, 0.0003, 2 | 100.0/0.0/100.0 | 27, 0.0004, 2 | NOT RUN | 2,890,000 |
| ZIP vs borough | 100.0/0.0/100.0 | 278, 0.0, 2 | 100.0/0.0/100.0 | 397, 0.0, 2 | NOT RUN | 2,968,400 |
| Complaint vs descriptor | 100.0/0.0/98.7 | 211, 0.0001, 2 | 100.0/0.0/98.6 | 182, 0.0001, 2 | NOT RUN | 2,938,600 |
| Resolution vs status | 100.0/0.0/78.5 | 81, 0.0001, 2 | 100.0/0.0/48.6 | 62, 0.0002, 2 | NOT RUN | 2,921,400 |
| PII in free text | 100.0/0.0/75.1 | 12, 0.0009, 2 | 0.0/0.0/100.0 | 15, 0.0007, 1 | NOT RUN | 2,923,867 |

Full per-row LLM review of every row for ONE check would send about **138,559,000 input tokens per million rows** (~139 tokens/row) - x12 checks if each is a separate call. Multiply by your Gemini price (`GEMINI_PRICE_IN_PER_M`) for dollars; we do not assume a price.

Reading the table (honest): rules and statistics tie on most types here; the clear separations are **null spike** (a rule on required columns only sees 4 of 5+ columns; the per-agency z-test sees any column) and **PII** (regex cannot see personal names, the shape heuristic can but would over-fire on real Title-Case free text - check FA on real data). Schema and dtype checks are set comparisons; the statistical family adds nothing there. Near-duplicates and ZIP/borough hinge on data: expect real data to show repeat-complaint false alarms for the near-dup rule.

## 3. Hybrid pipeline (Task 5)

Winner per type chosen automatically = max(detect - 2 x false-alarm), ties go to rules (cheaper, clearer alerts):

| Problem | Chosen | Hybrid detect % (mixed batches) | n | Hybrid FA % (clean) |
|---|---|---|---|---|
| Renamed/dropped column | rules | 100.0 | 10 | 0.0 |
| Column type change | rules | 100.0 | 10 | 0.0 |
| Date format switch | rules | 100.0 | 9 | 0.0 |
| Lat/lon swapped | rules | 100.0 | 8 | 0.0 |
| Exact duplicates | rules | 100.0 | 14 | 0.0 |
| Near-duplicates | rules | 100.0 | 8 | 0.0 |
| Null spike (one agency) | stats | 100.0 | 10 | 0.0 |
| Closed < created | rules | 100.0 | 2 | 0.0 |
| ZIP vs borough | rules | 100.0 | 13 | 0.0 |
| Complaint vs descriptor | rules | 100.0 | 7 | 0.0 |
| Resolution vs status | rules | 100.0 | 6 | 0.0 |
| PII in free text | rules | 100.0 | 6 | 0.0 |

End to end: **6,189 rows/s per core**, **$0.0018 CPU per million rows**, any-alert false-alarm on clean batches **0.0%**, LLM stage (second opinion on *alerted* semantic checks only, <=30 rows) projected **529,160 tokens per million rows** vs 138,559,000 for reviewing every row once. mixed batches have 1-3 simultaneous row-level corruptions; schema/dtype batches tested alone. LLM stage NOT RUN: tokens are what it would receive.

## 4. Scale and design (Task 6) - 50M rows/day, 120 customers

**Projection (from measured hybrid throughput, synthetic data, this machine; re-measure on yours):** average 579 rows/s, assumed 5x peak = 2,894 rows/s. At 6,189 rows/s/core that is **1 core(s) at peak** (1 on average); CPU cost/day = 50 x $0.0018 = **$0.090**. A 5000-row batch clears in ~808 ms. LLM confirmation tokens/day = 50 x 529,160 = **26,458,000 tokens** (only if every batch alerted at today's rate); reviewing every row with an LLM = 50 x 138,559,000 = **6,927,950,000 tokens per check per day** - not viable.

**What changes at scale, and why**
1. *Schemas*: 120 customers means 120 column vocabularies. A per-customer column-mapping layer (declarative, versioned) replaces hard-coded names; an LLM may *propose* the mapping once at onboarding or on schema drift (rare, cheap, human-approved) - never per row.
2. *Reference statistics become per-customer state*: ZIP-borough map, pair/allow-list, per-agency null baselines, duration norms are fitted per customer, versioned, and refreshed on a schedule with drift alarms. This is where statistics beats hand-written rules: nobody curates 120 allow-lists.
3. *Curated rules shrink to universal invariants* (types, ISO dates, closed>=created, coordinate bounds, dup keys); everything customer-specific is learned. Near-duplicate and duplicate detection must become cross-batch (keyed store / Bloom filter + time window), because a 5k-row batch cannot see a duplicate that arrived an hour ago.
4. *Alert thresholds calibrated per customer* from their own clean baseline (as done here), otherwise the false-alarm rate on legitimately repetitive customers swamps the team.
5. *Engine*: in-process pandas is fine for 1-2 cores of average load, but 120 tenants and 5x peaks call for columnar/vectorised execution (Arrow/DuckDB or Polars), batching by tenant, and horizontal workers; CPU stays a rounding error, so the real cost drivers are people (false alarms) and LLM tokens.
6. *LLM budget*: second opinion only on alerted rows of semantic checks (pair, resolution, PII, ZIP), capped per customer per day, plus a small random audit sample to measure rule drift. Per-row review of every row is ~3 orders of magnitude more tokens than the hybrid and is not justified by any measurement here.
7. *Unknown unknowns*: one cheap profile-drift statistic per column (distribution shift) as a catch-all instead of 12 x 120 bespoke checks.

*Caveats:* synthetic text inflates detection; LLM detection was not run; throughput numbers are from a sandbox, not a laptop; cost excludes engineering and storage.
