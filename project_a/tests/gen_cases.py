"""Generates tests/cases.json (>=200 cases, expected tax for BOTH regimes from tests/oracle.py) and the 30-case
official_check_template.csv"""
import json, random, csv
from pathlib import Path
from project_a.common import TaxInput
from project_a.tests.oracle import oracle

HERE = Path(__file__).parent
DELTAS = (-10, -1, 0, 1, 10)


def case(tag, **kw):
    i = TaxInput(**kw).d()
    o = oracle(i)
    return {"tag": tag, "input": i, "expected": {r: {"taxable_income": int(o[r][0]), "total_tax": int(o[r][1])} for r in o}}


def build():
    C = []
    # new-regime thresholds: slab edges, rebate limit, surcharge edges (taxable = T+delta => gross = taxable + 75k)
    NEWT = {"2024-25": [300000, 700000, 1000000, 1200000, 1500000, 5000000, 10000000, 20000000],
            "2025-26": [400000, 800000, 1200000, 1600000, 2000000, 2400000, 5000000, 10000000, 20000000]}
    for fy, ts in NEWT.items():
        for T in ts:
            for d in DELTAS:
                C.append(case(f"boundary-new-{fy}-{T}{d:+d}", fy=fy, age=30, gross_salary=T + d + 75000))
    # old-regime thresholds by age band (gross = taxable + 50k)
    OLDT = {30: [250000, 500000, 1000000, 5000000, 10000000, 20000000], 65: [300000, 500000, 1000000], 82: [500000, 1000000]}
    for age, ts in OLDT.items():
        for T in ts:
            for d in DELTAS:
                C.append(case(f"boundary-old-age{age}-{T}{d:+d}", fy="2024-25", age=age, gross_salary=T + d + 50000))
    for d in DELTAS:   # old regime is unchanged in FY25-26: spot check
        C.append(case(f"old-unchanged-25-26{d:+d}", fy="2025-26", age=35, gross_salary=500000 + d + 50000))
    # deduction caps (old regime), each +-1 around the cap
    for fy in ("2024-25", "2025-26"):
        for cap, k in ((150000, "inv_80c"), (50000, "nps_80ccd1b"), (200000, "home_loan_interest")):
            for d in (-1, 0, 1, 100000):
                C.append(case(f"cap-{k}-{fy}{d:+d}", fy=fy, age=40, gross_salary=2500000, **{k: cap + d}))
        for age, parents_senior, sc, pc in ((30, False, 25000, 25000), (30, True, 25000, 50000), (62, False, 50000, 25000), (62, True, 50000, 50000)):
            for d in (-1, 0, 1):
                C.append(case(f"cap-80d-{fy}-a{age}-ps{int(parents_senior)}{d:+d}", fy=fy, age=age, gross_salary=1800000,
                              health_self=sc + d, health_parents=pc + d, parents_senior=parents_senior))
    # HRA: each of the three limbs binding, metro and non-metro, plus no-rent / no-HRA
    for metro in (True, False):
        pct = 0.5 if metro else 0.4
        C.append(case(f"hra-actual-binds-metro{int(metro)}", age=30, gross_salary=1500000, basic=600000, hra_received=100000, rent_paid=400000, metro=metro))
        C.append(case(f"hra-rent-minus-10pct-binds-metro{int(metro)}", age=30, gross_salary=1500000, basic=600000, hra_received=300000, rent_paid=180000, metro=metro))
        C.append(case(f"hra-pct-basic-binds-metro{int(metro)}", age=30, gross_salary=1500000, basic=600000, hra_received=400000, rent_paid=500000, metro=metro))
        C.append(case(f"hra-rent-below-10pct-metro{int(metro)}", age=30, gross_salary=1500000, basic=600000, hra_received=300000, rent_paid=50000, metro=metro))
    C.append(case("hra-no-rent", age=30, gross_salary=1500000, basic=600000, hra_received=300000))
    C.append(case("hra-rent-no-hra", age=30, gross_salary=1500000, basic=600000, rent_paid=240000, metro=True))
    # degenerate / extreme
    for g in (0, 1, 49999, 50000, 50001, 74999, 75000, 75001, 5000000, 10000000, 100000000, 600000000):
        C.append(case(f"edge-gross-{g}", age=30, gross_salary=g))
    C.append(case("deductions-exceed-income", age=30, gross_salary=300000, inv_80c=150000, nps_80ccd1b=50000, home_loan_interest=200000, health_self=25000))
    C.append(case("loan-interest-exceeds-salary", age=30, gross_salary=100000, home_loan_interest=200000))
    # seeded random "realistic" profiles
    rnd = random.Random(2025)
    for n in range(60):
        g = rnd.choice([rnd.randint(3, 40) * 100000, rnd.randint(40, 300) * 100000, rnd.randint(300, 900) * 100000])
        basic = int(g * rnd.uniform(0.3, 0.55)) // 1000 * 1000
        rent = rnd.choice([0, rnd.randint(1, 15) * 20000]) 
        C.append(case(f"random-{n}", fy=rnd.choice(["2024-25", "2025-26"]), age=rnd.choice([24, 31, 45, 59, 60, 67, 79, 80, 85]),
                      gross_salary=g, basic=basic, hra_received=int(basic * rnd.uniform(0.2, 0.5)) if rent else 0, rent_paid=rent,
                      metro=rnd.random() < .5, inv_80c=rnd.choice([0, 50000, 150000, 190000]), nps_80ccd1b=rnd.choice([0, 50000, 60000]),
                      health_self=rnd.choice([0, 12000, 25000, 55000]), health_parents=rnd.choice([0, 20000, 50000, 70000]),
                      parents_senior=rnd.random() < .5, home_loan_interest=rnd.choice([0, 120000, 240000])))
    return C


def main():
    C = build()
    (HERE / "cases.json").write_text(json.dumps(C, indent=1))
    rnd = random.Random(7)
    pick = rnd.sample(C, 30)
    with open(HERE / "official_check_template.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tag", "fy", "age", "gross_salary", "basic", "hra_received", "rent_paid", "metro", "inv_80c", "nps_80ccd1b",
                    "health_self", "health_parents", "parents_senior", "home_loan_interest",
                    "our_old_tax", "our_new_tax", "official_old_tax", "official_new_tax", "match?"])
        for c in pick:
            i = c["input"]
            w.writerow([c["tag"]] + [i[k] for k in ("fy", "age", "gross_salary", "basic", "hra_received", "rent_paid", "metro", "inv_80c",
                                                    "nps_80ccd1b", "health_self", "health_parents", "parents_senior", "home_loan_interest")]
                       + [c["expected"]["old"]["total_tax"], c["expected"]["new"]["total_tax"], "", "", ""])
    print(len(C), "cases written")


if __name__ == "__main__":
    main()
