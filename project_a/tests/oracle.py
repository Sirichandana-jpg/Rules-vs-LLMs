from fractions import Fraction as F

NEW = {
    "FY2024-25": dict(starts=[(0, 0), (300000, 5), (700000, 10), (1000000, 15), (1200000, 20), (1500000, 30)],
                      std=75000, reb_lim=700000, reb_max=25000),
    "FY2025-26": dict(starts=[(0, 0), (400000, 5), (800000, 10), (1200000, 15), (1600000, 20), (2000000, 25), (2400000, 30)],
                      std=75000, reb_lim=1200000, reb_max=60000),
}
SUR = [(5_000_000, 10), (10_000_000, 15), (20_000_000, 25), (50_000_000, 37)]


def cum_tax(income, starts):
    """tax = sum_i rate_i * (min(income, start_{i+1}) - start_i)  -- via differences of rates."""
    t = F(0)
    prev_rate = 0
    for s, r in starts:
        if income > s:
            t += F(r - prev_rate, 100) * (income - s)
        prev_rate = r
    return t


def old_starts(exempt):
    return [(0, 0), (exempt, 5), (500000, 20), (1000000, 30)] if exempt < 500000 else [(0, 0), (500000, 20), (1000000, 30)]


def r10(x):
    return int((x + 5) // 10) * 10


def surcharge_rate(inc, cap25):
    r = 0
    for t, rt in SUR:
        if inc > t:
            r = rt
    return min(r, 25) if cap25 else r


def finish(taxable, starts, reb_lim, reb_max, reb_mr, cap25):
    tax = cum_tax(taxable, starts)
    if taxable <= reb_lim:
        tax = max(F(0), tax - reb_max)
    elif reb_mr:
        tax = min(tax, F(taxable - reb_lim))
    rate = surcharge_rate(taxable, cap25)
    total = tax * (100 + rate) / 100
    if rate:
        T = max(t for t, _ in SUR if taxable > t)
        base = cum_tax(T, starts)
        base_total = base * (100 + surcharge_rate(T, cap25)) / 100
        total = min(total, base_total + (taxable - T))
    return r10(total * 104 / 100)


def expected(d, fy):
    g = d["gross_salary"]
    n = NEW[fy]
    ti_new = r10(F(g - min(g, n["std"])))
    new = finish(ti_new, n["starts"], n["reb_lim"], n["reb_max"], True, True)
    age = d.get("age", 30)
    hra = 0
    if d.get("hra_received", 0) > 0 and d.get("rent_paid", 0) > 0:
        b = d.get("basic_da", 0)
        hra = max(F(0), min(F(d["hra_received"]), F(d["rent_paid"]) - F(b, 10), F(b * (50 if d.get("metro") else 40), 100)))
    s = g - hra
    s -= min(s, 50000)
    gti = max(F(0), s - min(d.get("home_loan_interest", 0), 200000))
    capself = 50000 if age >= 60 else 25000
    cappar = 50000 if d.get("parents_senior") else 25000
    ded = min(d.get("section_80c", 0), 150000) + min(d.get("nps_80ccd1b", 0), 50000) \
        + min(d.get("health_self", 0), capself) + min(d.get("health_parents", 0), cappar)
    ti_old = r10(max(F(0), gti - min(gti, ded)))
    exempt = 500000 if age >= 80 else 300000 if age >= 60 else 250000
    old = finish(ti_old, old_starts(exempt), 500000, 12500, False, False)
    return {"tax_old": old, "tax_new": new, "ti_old": ti_old, "ti_new": ti_new,
            "recommended": "old" if old < new else "new", "savings": abs(old - new)}


def oracle(i):
    """Adapter from the TaxInput dict used by project_a.common to the reference formulas above."""
    fy = "FY" + i["fy"]
    d = {"gross_salary": i["gross_salary"], "age": i["age"], "basic_da": i.get("basic", 0),
         "hra_received": i.get("hra_received", 0), "rent_paid": i.get("rent_paid", 0), "metro": i.get("metro", False),
         "section_80c": i.get("inv_80c", 0), "nps_80ccd1b": i.get("nps_80ccd1b", 0), "health_self": i.get("health_self", 0),
         "health_parents": i.get("health_parents", 0), "parents_senior": i.get("parents_senior", False),
         "home_loan_interest": i.get("home_loan_interest", 0)}
    e = expected(d, fy)
    return {"old": (e["ti_old"], e["tax_old"]), "new": (e["ti_new"], e["tax_new"])}
