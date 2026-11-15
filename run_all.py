"""ONE COMMAND reproduces every reported number:  python run_all.py [--fetch]
--fetch downloads real NYC 311 2023 first (needs internet). Set GEMINI_API_KEY to also run the LLM paths."""
import subprocess, sys
fetch = "--fetch" in sys.argv
steps = [[sys.executable, "-m", "project_a.tests.gen_cases"],
         [sys.executable, "-m", "unittest", "project_a.tests.test_golden", "project_b.tests.test_b", "-v"],
         [sys.executable, "-m", "project_a.evaluate"], [sys.executable, "-m", "project_a.report_a"]]
if fetch: steps.append([sys.executable, "-m", "project_b.fetch_311"])
steps += [[sys.executable, "-m", "project_b.profile"], [sys.executable, "-m", "project_b.evaluate"],
          [sys.executable, "-m", "project_b.report_b"], [sys.executable, "make_decision_matrix.py"]]
for s in steps:
    print(">>", " ".join(s[1:])); r = subprocess.run(s)
    if r.returncode: sys.exit(r.returncode)
print("\nDone. See RESULTS_A.md, RESULTS_B.md, DECISION_MATRIX.md")
