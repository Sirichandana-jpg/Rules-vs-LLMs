
# AI_USAGE.md

## AI Tools Used

- **Claude (claude.ai and code-execution sandbox):** Used extensively during development to assist with implementing the project architecture, writing and debugging Python modules, evaluating implementations, and preparing technical documentation.

- **ChatGPT:** Used for additional technical clarification, reviewing implementation decisions, understanding errors, refining documentation, and improving the presentation of the final submission.

- **Google Gemini:** Integrated as the LLM backend for the query-time tax calculation, natural-language parsing, and data-quality detection components. However, Gemini API calls were not executed during development because the execution environment did not have internet access or an API key. These components are explicitly marked as `NOT RUN`; no simulated results are presented as actual measurements.

## How AI Was Used

### Project A – Income Tax Calculation Engine

AI assistance was used for:
- Developing and refining the three implementation approaches: hand-coded rules, query-time LLM, and LLM-compiled rules.
- Assisting with the DSL design and rule compilation workflow.
- Generating test scenarios, including boundary conditions and edge cases.
- Implementing and reviewing the natural-language input parser.
- Debugging calculation and validation logic.
- Preparing comparison reports and documenting trade-offs.

The deterministic calculation engines and their test results were validated through the available test suite, including 277 test cases, 12 hand-computed golden cases, and repeated execution tests.

### Project B – Data Quality Detection System

AI assistance was used for:
- Designing the data profiling and corruption-injection workflow.
- Implementing and refining rule-based, statistical, and LLM-based detector components.
- Developing the hybrid detection pipeline.
- Assisting with evaluation metrics and performance analysis.
- Preparing the scalability analysis and technical documentation.

The implemented rule-based and statistical components were evaluated using the available real and synthetic datasets. Gemini-based detection was implemented but not executed.

## Human Verification and Responsibility

AI-generated code and suggestions were not treated as automatically correct. The implementation was reviewed, modified, and validated through:

- Unit tests and hand-computed test cases.
- Cross-checking independent calculation implementations.
- Comparing expected and actual outputs.
- Testing boundary conditions and failure scenarios.
- Reviewing detection metrics, false alarms, execution time, and computational cost.
- Checking that unexecuted LLM components were clearly reported as `NOT RUN`.

All final architectural decisions, interpretation of results, trade-offs, and conclusions were reviewed before submission.

## One Instance Where AI Was Wrong

During development, the AI incorrectly assumed that the working directory was empty and created new files without first checking the existing project structure.

As a result, two existing test files (`project_a/tests/oracle.py` and `project_a/tests/test_golden.py`) were overwritten.

This was identified through an import-resolution check, which revealed that the expected oracle module was missing.

**Correction:** Both files were reconstructed and validated by regenerating all 277 expected values in `cases.json`, with zero mismatches. The 12 hand-computed golden cases were also rerun against both deterministic calculation engines.

This incident reinforced the importance of inspecting existing code, reviewing AI-generated changes, and independently validating the final implementation.

## Limitations

- Gemini API-dependent components were not executed because API access was unavailable.
- LLM performance results are not presented as measured results.
- Project B uses synthetic corruption scenarios for controlled evaluation; results should not be interpreted as guaranteed production performance.
- AI-generated implementations and documentation were subject to review and validation.

**Final Responsibility:** AI tools assisted the development process, but the submitted implementation, evaluation methodology, interpretation of results, and final decisions were reviewed by the candidate.
