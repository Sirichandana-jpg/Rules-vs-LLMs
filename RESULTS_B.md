
# RESULTS_B — Data Quality Detection: Rules vs. Statistics vs. LLM

**Dataset:** NYC 311 Service Requests  
**Source:** NYC Open Data (`erm2-nwe9`)  
**Time period:** Records created during calendar year 2023  
**Data classification:** REAL dataset unless explicitly identified as synthetic.

---

## 1. Real Data Quality Problems (Task 1)

A total of **219,000 rows** were profiled from the NYC 311 Service Requests dataset.

The complete profiling results are available in `project_b/profile_b.json`.

| Data Quality Problem | Rows Affected | Percentage | Example Unique Keys |
|---|---:|---:|---|
| `closed_date` earlier than `created_date` | 204 | 0.093% | 56454589, 56454607, 56477303 |
| `closed_date` equals `created_date` (zero-length) | 2,941 | 1.343% | 56412696, 56412810, 56413014 |
| Status = Closed but `closed_date` is NULL | 1,210 | 0.553% | 57896350, 57944220, 57962855 |
| `closed_date` present but status is not Closed | 231 | 0.105% | 56435292, 56435352, 56454062 |
| Latitude/longitude missing | 2,726 | 1.245% | 56408061, 56412433, 56412512 |
| `incident_zip` missing | 2,381 | 1.087% | 56408061, 56412433, 56412512 |
| ZIP prefix implies a different borough | 51 | 0.023% | 56453999, 56487199, 56540638 |
| Borough = `UNSPECIFIED` or missing | 198 | 0.090% | 56419618, 56419743, 56419755 |
| Phone/email pattern in free text | 5,471 | 2.498% | 56412539, 56412602, 56412618 |
| Complaint type: same value with different case/whitespace | 977 | 0.446% | 56412498, 56412539, 56412618 |
| Descriptor: same value with different case/whitespace | 143 | 0.065% | 56412496, 56419789, 56435239 |

---

## 2. Detection Performance, False Alarms and Cost (Tasks 3–4)

### Evaluation Metrics

- **Detect:** Percentage of corrupted batches correctly alerted.
- **FA:** Percentage of clean batches incorrectly alerted (false-alarm rate).
- **Rec:** Row-level recall.
- **Throughput:** Thousands of rows processed per second (`k rows/s`), measured in-process on the evaluation machine. Batch-level schema checks are constant-time and are shown with capped throughput.
- **Cost ($/M):** CPU cost per million rows.
- **Expl:** Explainability score (0–2):
  - 2 = Row-level evidence and expected value.
  - 1 = Batch-level metric.
  - 0 = Score only.

### Rules vs. Statistical Detection vs. LLM

| Data Quality Problem | Rules: Detect / FA / Rec | Rules: k rows/s / $/M / Expl | Stats: Detect / FA / Rec | Stats: k rows/s / $/M / Expl | LLM (Gemini) | LLM Tokens/M Rows |
|---|---|---|---|---|---|---:|
| Renamed/dropped column | 100.0 / 0.0 / - | 83,808 / 0.0 / 2 | 100.0 / 0.0 / - | 99,999 / 0.0 / 1 | NOT RUN | 619,067 |
| Column type change | 100.0 / 0.0 / - | 17,138 / 0.0 / 2 | 100.0 / 0.0 / - | 890 / 0.0 / 1 | NOT RUN | 673,533 |
| Date format switch | 100.0 / 0.0 / 100.0 | 140 / 0.0001 / 2 | 100.0 / 0.0 / 100.0 | 55 / 0.0002 / 2 | NOT RUN | 642,267 |
| Latitude/longitude swapped | 100.0 / 0.0 / 100.0 | 5,214 / 0.0 / 2 | 100.0 / 0.0 / 100.0 | 5,804 / 0.0 / 2 | NOT RUN | 2,927,667 |
| Exact duplicates | 100.0 / 0.0 / 100.0 | 458 / 0.0 / 2 | 100.0 / 0.0 / 100.0 | 37 / 0.0003 / 2 | NOT RUN | 2,977,067 |
| Near-duplicates | 100.0 / 0.0 / 100.0 | 32 / 0.0003 / 2 | 100.0 / 0.0 / 98.8 | 28 / 0.0004 / 2 | NOT RUN | 2,967,400 |
| Null spike (one agency) | 35.0 / 0.0 / 35.0 | 1,033 / 0.0 / 2 | 100.0 / 0.0 / 100.0 | 100 / 0.0001 / 2 | NOT RUN | 2,916,200 |
| Closed < created | 100.0 / 0.0 / 100.0 | 39 / 0.0003 / 2 | 100.0 / 0.0 / 100.0 | 27 / 0.0004 / 2 | NOT RUN | 2,890,000 |
| ZIP vs. borough | 100.0 / 0.0 / 100.0 | 278 / 0.0 / 2 | 100.0 / 0.0 / 100.0 | 397 / 0.0 / 2 | NOT RUN | 2,968,400 |
| Complaint vs. descriptor | 100.0 / 0.0 / 98.7 | 211 / 0.0001 / 2 | 100.0 / 0.0 / 98.6 | 182 / 0.0001 / 2 | NOT RUN | 2,938,600 |
| Resolution vs. status | 100.0 / 0.0 / 78.5 | 81 / 0.0001 / 2 | 100.0 / 0.0 / 48.6 | 62 / 0.0002 / 2 | NOT RUN | 2,921,400 |
| PII in free text | 100.0 / 0.0 / 75.1 | 12 / 0.0009 / 2 | 0.0 / 0.0 / 100.0 | 15 / 0.0007 / 1 | NOT RUN | 2,923,867 |

**Important:** Gemini-based LLM detection was not executed. Token counts represent projected usage based on sampled review, not measured API execution.

### LLM Token Cost Analysis

Reviewing every row with an LLM for just ONE check would require approximately:

**138,559,000 input tokens per million rows** (approximately 139 tokens per row).

If all 12 checks were performed as separate calls, the token requirement would increase proportionally.

To calculate the estimated API cost:

`Estimated Cost = (Total Input Tokens / 1,000,000) × GEMINI_PRICE_IN_PER_M`

No Gemini API price is assumed in this evaluation.

### Key Observations

1. **Rules and statistics perform similarly:** Both approaches achieve strong detection results across most evaluated data-quality problems.

2. **Null spike detection:** Statistical detection performs better than the implemented rule-based approach. The rule checks required columns and detects only 35% of corrupted batches, whereas the per-agency statistical test detects 100%.

3. **PII detection:** Regex-based rules achieve 75.1% row-level recall. The statistical approach achieves 100% recall but has lower explainability (score 1).

4. **Schema and data-type checks:** These are fundamentally set-comparison problems. Statistical detection provides little additional value over deterministic rules.

5. **Near-duplicate detection:** Both methods achieve strong detection, but real datasets may contain legitimate repeated complaints, potentially creating false alarms.

6. **LLM limitations:** Gemini was not executed, so its projected token requirements should not be interpreted as measured detection performance.

---

## 3. Hybrid Detection Pipeline (Task 5)

The hybrid pipeline automatically selects the best detector for each problem using the following scoring function:

`Score = Detect Rate - 2 × False Alarm Rate`

When scores are tied, rules are preferred because they are cheaper and provide clearer alerts.

### Selected Detector Per Problem

| Data Quality Problem | Selected Detector | Hybrid Detection (%) | Sample Count (n) | Hybrid False Alarm (%) |
|---|---|---:|---:|---:|
| Renamed/dropped column | Rules | 100.0 | 10 | 0.0 |
| Column type change | Rules | 100.0 | 10 | 0.0 |
| Date format switch | Rules | 100.0 | 9 | 0.0 |
| Latitude/longitude swapped | Rules | 100.0 | 8 | 0.0 |
| Exact duplicates | Rules | 100.0 | 14 | 0.0 |
| Near-duplicates | Rules | 100.0 | 8 | 0.0 |
| Null spike (one agency) | Statistics | 100.0 | 10 | 0.0 |
| Closed < created | Rules | 100.0 | 2 | 0.0 |
| ZIP vs. borough | Rules | 100.0 | 13 | 0.0 |
| Complaint vs. descriptor | Rules | 100.0 | 7 | 0.0 |
| Resolution vs. status | Rules | 100.0 | 6 | 0.0 |
| PII in free text | Rules | 100.0 | 6 | 0.0 |

### End-to-End Hybrid Performance

| Metric | Result |
|---|---:|
| Throughput per core | 6,189 rows/second |
| CPU cost per million rows | $0.0018 |
| False-alarm rate on clean batches | 0.0% |
| LLM confirmation tokens per million rows | 529,160 |
| Full LLM review tokens per million rows (one check) | 138,559,000 |

**Hybrid pipeline design:**

- Rules handle most deterministic data-quality checks.
- Statistical detection handles agency-specific null spikes.
- The LLM stage is designed as a second opinion for alerted semantic checks, limited to a maximum of 30 rows.
- Gemini execution was NOT RUN. Token figures are projected estimates.

The hybrid approach reduces projected LLM usage from 138,559,000 tokens to 529,160 tokens per million rows compared with reviewing every row for one check.

Mixed batches contain 1–3 simultaneous row-level corruptions. Schema and data-type corruption batches were tested separately.

---

## 4. Scalability and System Design (Task 6)

### Target Scenario

| Parameter | Value |
|---|---:|
| Daily data volume | 50 million rows |
| Number of customers | 120 |
| Average processing rate | 579 rows/second |
| Assumed peak multiplier | 5× |
| Peak processing rate | 2,894 rows/second |
| Measured hybrid throughput | 6,189 rows/second/core |
| Estimated peak CPU requirement | 1 core |
| Estimated average CPU requirement | 1 core |
| CPU cost per million rows | $0.0018 |
| Estimated daily CPU cost | $0.090 |

### Processing and LLM Cost Projection

Based on the measured hybrid throughput and synthetic-data evaluation:

- Average throughput required: approximately 579 rows/second.
- Peak throughput required (5×): approximately 2,894 rows/second.
- At 6,189 rows/second per core, the estimated peak requirement is 1 core.
- A batch of 5,000 rows takes approximately 808 ms at the measured throughput.

**Daily LLM token projection:**

| Processing Strategy | Estimated Tokens per Million Rows | Estimated Tokens per Day |
|---|---:|---:|
| Hybrid LLM confirmation | 529,160 | 26,458,000 |
| Full LLM review (one check) | 138,559,000 | 6,927,950,000 |

The hybrid LLM estimate assumes every batch triggers the LLM confirmation stage at the projected rate. Actual usage would depend on the number of alerts.

Full LLM review is approximately three orders of magnitude more expensive in token consumption than the hybrid approach.

### What Changes at Scale, and Why?

**1. Customer-specific schema management**

With 120 customers, each customer may have a different column vocabulary. A declarative, versioned column-mapping layer should replace hard-coded column names.

An LLM may propose mappings during onboarding or schema changes, but all mappings should be human-approved rather than generated for every row.

**2. Customer-specific reference statistics**

Reference statistics such as ZIP-to-borough mappings, allowed value pairs, per-agency null baselines, and duration norms should be maintained separately for each customer.

These baselines should be versioned, periodically refreshed, and monitored for drift.

Statistical detection becomes particularly useful because manually maintaining 120 different allow-lists is difficult.

**3. Universal rules and learned customer-specific behaviour**

Rules should focus on universal invariants:

- Data types.
- ISO date formats.
- `closed_date >= created_date`.
- Coordinate boundaries.
- Duplicate keys.

Customer-specific patterns should be learned from historical data.

Duplicate and near-duplicate detection should also work across batches using a keyed store or Bloom filter with a time window. A single 5,000-row batch cannot detect duplicates that arrived an hour earlier.

**4. Customer-specific alert thresholds**

Alert thresholds should be calibrated using each customer's clean baseline.

Without customer-specific calibration, legitimate repetitive records may generate excessive false alarms.

**5. Processing architecture**

In-process pandas execution is sufficient for the measured 1–2-core average workload.

However, 120 tenants and 5× peak traffic require a more scalable architecture:

- Columnar and vectorised execution using Arrow, DuckDB, or Polars.
- Batching by tenant.
- Horizontally scalable processing workers.
- Efficient data partitioning and parallel execution.

CPU processing cost is relatively small. The more important operational costs are false alarms, human investigation, and LLM token consumption.

**6. LLM budget management**

LLMs should be used only as a second opinion for alerted semantic checks, such as:

- Complaint and descriptor inconsistencies.
- Resolution and status mismatches.
- PII detection.
- ZIP and borough inconsistencies.

Usage should be capped per customer per day, with a small random audit sample to monitor rule drift.

Full per-row LLM review is not justified by the measured results.

**7. Unknown data-quality problems**

Introduce one inexpensive profile-drift statistic per column as a general mechanism for identifying unexpected distribution changes.

This provides a catch-all mechanism without requiring 12 × 120 separate custom checks.

---

## 5. Limitations and Experimental Caveats

The following limitations should be considered when interpreting the results:

1. **Synthetic corruption:** Synthetic text corruption may inflate detection performance compared with real-world data.

2. **LLM execution:** Gemini-based detection was not executed. All LLM detection results are marked `NOT RUN`; token values are projections.

3. **Hardware dependency:** Throughput measurements were obtained in a sandbox environment and may differ on other machines.

4. **Cost assumptions:** CPU cost is based on the assumed rate of $0.04 per vCPU-hour. It excludes engineering, storage, and other infrastructure expenses.

5. **Dataset scope:** Real-data profiling was performed on 219,000 NYC 311 records created during 2023. Results may differ across datasets and time periods.

6. **Scalability projections:** The 50-million-rows-per-day scenario is a projection based on measured hybrid throughput and synthetic evaluation, not a production deployment benchmark.

7. **False alarms:** Zero false alarms were observed in the evaluated clean batches. This does not guarantee zero false alarms in production.

---

## 6. Final Conclusion

The evaluation demonstrates that a hybrid data-quality detection architecture provides a practical balance between deterministic rules, statistical analysis, and LLM-assisted semantic validation.

- **Rules** are effective for schema validation, data-type checks, date consistency, duplicate detection, and universal data constraints.
- **Statistical methods** provide additional value for detecting distribution changes and customer-specific anomalies, particularly null spikes.
- **LLMs** can potentially assist with semantic validation and schema interpretation, but their execution, cost, and detection performance require further validation.

The recommended architecture uses deterministic rules as its foundation, statistical detection for customer-specific anomalies, and LLMs selectively as an optional second-opinion layer.

This design prioritises explainability, predictable performance, low computational cost, and scalability across multiple customers.
