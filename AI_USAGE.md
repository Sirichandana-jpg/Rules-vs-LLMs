# AI_USAGE

**Tools:** Claude (claude.ai chat, code-execution sandbox) wrote and ran the code, tests and documents in this repo.
Gemini (free tier) is wired in for the LLM paths (`common/gemini.py`, `project_a/calc_llm.py`, `project_a/parser.py::llm_parse`,
`project_b/detectors/llm.py`) but was **not run** while building (sandbox had no internet / API key). Every LLM cell in
RESULTS_A.md / RESULTS_B.md says `NOT RUN` rather than a simulated value.

**What AI did:** engines for all three Project A designs, test-suite generator + oracle, plain-language parser, Project B
injector / three detector families / hybrid pipeline, report generators, this documentation.
**What the AI could not do:** download NYC 311 data, call Gemini, or use the official ITD calculator. Those steps are listed
in README.md as to-dos for the candidate.

## One place the AI was wrong, and how it was caught
While finishing the repo, the AI assumed the working directory was empty and wrote new files into it. Two files already
existed (`project_a/tests/oracle.py`, `project_a/tests/test_golden.py`) and were overwritten and lost. It was caught by an
import-resolution scan that showed `gen_cases.py` importing a module that no longer existed (`project_a.tests.oracle`).
Repair: both files were rewritten (headers say "RECONSTRUCTED") and **validated by regenerating all 277 expected values in
`cases.json` - 0 mismatches** - and re-running the 12 hand-computed golden cases through both deterministic engines.

