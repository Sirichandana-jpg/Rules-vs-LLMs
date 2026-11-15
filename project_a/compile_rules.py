import sys, json
from common import gemini
from .common import ROOT, TaxInput, load_json
from . import calc_compiled

SPEC = """Output JSON {"fy":..., "tables":{name:[[upper_limit_or_null, rate_pct],...]}, "regimes":{"old":[steps],"new":[steps]}}.
Each step: {"id","clause","expr"}; expr is a Python-syntax expression using: +,-,*,/, comparisons, `a if c else b`, and/or/not,
min, max, round10(x), slab_tax(table_name, x), sur_rate(table_name, x), thresh(table_name, x), earlier step ids, and these inputs:
fy, age, gross_salary, basic, hra_received, rent_paid, metro, inv_80c, nps_80ccd1b, health_self, health_parents, parents_senior, home_loan_interest.
Required final step ids: ti (taxable income, rounded) and total (tax payable, rounded). `clause` must be a [tag] from the rules.
Surcharge tables list [threshold, pct] and apply when income EXCEEDS the threshold. Mirror this reference example's structure exactly:
"""


def main(fy, selftest=False):
    rules = (ROOT / "rule_text" / f"fy{fy.replace('-', '_')}.md").read_text()
    ref = (ROOT / "compiled" / "fy2024_25.json").read_text()
    out = gemini.generate(SPEC + ref + "\n\nRULES:\n" + rules, cache=False)
    cand = gemini.parse_json(out["text"])
    p = ROOT / "compiled" / f"fy{fy.replace('-', '_')}.candidate.json"
    p.write_text(json.dumps(cand, indent=1)); print("wrote", p, "- REVIEW THEN RENAME")
    if selftest:
        cases = [c for c in json.load(open(ROOT / "tests" / "cases.json")) if c["input"]["fy"] == fy]
        calc_compiled.load_compiled = lambda _fy: cand
        ok = sum(all(calc_compiled.calculate(TaxInput(**c["input"]))[r]["total_tax"] == c["expected"][r]["total_tax"] for r in ("old", "new")) for c in cases)
        print(f"candidate passes {ok}/{len(cases)} cases")


if __name__ == "__main__":
    main(sys.argv[1], "--selftest" in sys.argv)
