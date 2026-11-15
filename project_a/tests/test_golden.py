import json, unittest
from pathlib import Path
from project_a.common import TaxInput
from project_a import calc_rules, calc_compiled
from project_a.tests.oracle import oracle

# (fy, input kwargs, expected old tax or None, expected new tax or None, why)
G = [
    ("2024-25", dict(gross_salary=1_275_000), None, 83_200, "new 12L taxable: 20k+30k+30k=80k +4% cess"),
    ("2024-25", dict(gross_salary=775_000), None, 0, "new 7L taxable: tax 20k fully rebated"),
    ("2024-25", dict(gross_salary=785_000), None, 10_400, "new 7.1L: marginal relief caps tax at 10,000, +cess 400"),
    ("2024-25", dict(gross_salary=550_000), 0, None, "old 5L taxable: 12,500 rebated"),
    ("2024-25", dict(gross_salary=560_000), 15_080, None, "old 5.1L: 12,500+2,000=14,500 +4%"),
    ("2024-25", dict(gross_salary=1_000_000, inv_80c=150_000), 75_400, None, "old 8L: 12.5k+60k=72.5k +4%"),
    ("2024-25", dict(gross_salary=10_000_000), None, 3_051_620, "new 99.25L: 10% surcharge, no relief"),
    ("2024-25", dict(gross_salary=1_200_000, basic=500_000, hra_received=240_000, rent_paid=240_000, metro=True),
     108_680, None, "HRA=min(2.4L,1.9L,2.5L)=1.9L; old ti 9.6L"),
    ("2024-25", dict(gross_salary=5_085_000), None, 1_248_000, "new 50.1L: surcharge marginal relief -> 12L+10k, +4%"),
    ("2025-26", dict(gross_salary=1_275_000), None, 0, "FY25-26 12L taxable: fully rebated (60k)"),
    ("2025-26", dict(gross_salary=1_285_000), None, 10_400, "FY25-26 12.1L: marginal relief"),
    ("2025-26", dict(gross_salary=2_475_000), None, 312_000, "FY25-26 24L: 20k+40k+60k+80k+100k=300k +4%"),
]


class Golden(unittest.TestCase):
    def test_golden(self):
        for fy, kw, old, new, why in G:
            inp = TaxInput(fy=fy, **kw)
            outs = {"rules": calc_rules.calculate(inp), "compiled": calc_compiled.calculate(inp)}
            o = oracle(inp.d())
            outs["oracle"] = {"old": {"total_tax": o["old"][1]}, "new": {"total_tax": o["new"][1]}}
            for name, r in outs.items():
                if old is not None:
                    self.assertEqual(r["old"]["total_tax"], old, f"{name} old: {why}")
                if new is not None:
                    self.assertEqual(r["new"]["total_tax"], new, f"{name} new: {why}")

    def test_full_suite_all_engines_agree(self):
        cases = json.loads((Path(__file__).parent / "cases.json").read_text())
        self.assertGreaterEqual(len(cases), 200)
        for c in cases:
            inp = TaxInput(**c["input"])
            for name, r in (("rules", calc_rules.calculate(inp)), ("compiled", calc_compiled.calculate(inp))):
                for reg in ("old", "new"):
                    self.assertEqual((r[reg]["taxable_income"], r[reg]["total_tax"]),
                                     (c["expected"][reg]["taxable_income"], c["expected"][reg]["total_tax"]), (name, c["tag"], reg))


if __name__ == "__main__":
    unittest.main()
