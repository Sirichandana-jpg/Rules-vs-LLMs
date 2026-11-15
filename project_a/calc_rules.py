"""Implementation (a): hand-coded rules. Law lives in rules/fyYYYY_YY.json; this engine holds only the logic."""
from fractions import Fraction as F
from .common import *


def load_cfg(fy):
    p = ROOT / "rules" / f"fy{fy.replace('-', '_')}.json"
    if not p.exists():
        raise KeyError(f"No rules for FY {fy}")      # loud failure on purpose
    return load_json(p)


def calc_regime(inp: TaxInput, cfg, regime):
    tr = []

    def add(item, amt, clause):
        tr.append({"item": item, "amount": num(amt), "clause": clause}); return F(amt)

    g = inp.gross_salary
    add("gross salary", g, "Sec 15-17 salary")
    std = add("standard deduction", min(cfg["standard_deduction"][regime], g), "Sec 16(ia)")
    hra = hp = ded = F(0)
    if regime == "old":
        h = cfg["hra"]
        if inp.rent_paid > 0 and inp.hra_received > 0:
            pct = h["metro_pct"] if inp.metro else h["nonmetro_pct"]
            hra = max(F(0), min(F(inp.hra_received), inp.rent_paid - F(h["rent_less_basic_pct"], 100) * inp.basic,
                                F(pct, 100) * inp.basic))
        add("HRA exemption", hra, "Sec 10(13A); Rule 2A")
        hp = add("home-loan interest (self-occupied)", min(inp.home_loan_interest, cfg["caps"]["home_loan_interest"]), "Sec 24(b)")
        gti = g - hra - std - hp
        c = cfg["caps"]
        d80c = min(inp.inv_80c, c["80c"])
        d1b = min(inp.nps_80ccd1b, c["80ccd1b"])
        ds = min(inp.health_self, c["80d_self_senior"] if inp.age >= 60 else c["80d_self"])
        dp = min(inp.health_parents, c["80d_parents_senior"] if inp.parents_senior else c["80d_parents"])
        add("80C", d80c, "Sec 80C"); add("80CCD(1B)", d1b, "Sec 80CCD(1B)")
        add("80D self", ds, "Sec 80D"); add("80D parents", dp, "Sec 80D")
        ded = min(d80c + d1b + ds + dp, max(gti, F(0)))
        add("Chapter VI-A deductions allowed", ded, "Sec 80A(2) overall cap")
        table = "old_general" if inp.age < 60 else ("old_senior" if inp.age < 80 else "old_super_senior")
    else:
        gti = g - std
        table = "new"
    add("gross total income", gti, "Sec 14")
    ti = round10(max(gti - ded, 0))
    add("taxable income (rounded)", ti, "Sec 288A")
    slabs = cfg["slabs"][table]
    tax = add("tax on slabs", slab_tax(ti, slabs), "Sec 115BAC(1A)" if regime == "new" else "Finance Act First Schedule Pt I (slab rates)")
    rb = cfg["rebate_87a"][regime]
    rebate = F(0)
    if ti <= rb["limit"]:
        rebate = min(tax, F(rb["max"]))
    elif rb["marginal_relief"]:
        rebate = max(F(0), tax - (ti - rb["limit"]))
    add("rebate / marginal relief u/s 87A", rebate, "Sec 87A")
    t0 = tax - rebate
    tiers = cfg["surcharge"][regime]
    r, T = sur_rate(ti, tiers), thresh(ti, tiers)
    post = t0 * (1 + F(r, 100))
    if T:
        post = min(post, slab_tax(T, slabs) * (1 + F(sur_rate(T, tiers), 100)) + (ti - T))
    add("surcharge after marginal relief", post - t0, "Finance Act First Schedule Pt I (surcharge)")
    cess = add("health & education cess", post * F(cfg["cess_pct"], 100), "Finance Act cess 4%")
    total = round10(post + cess)
    add("total tax payable (rounded)", total, "Sec 288B")
    return {"taxable_income": ti, "total_tax": total, "trace": tr}


def calculate(inp: TaxInput):
    cfg = load_cfg(inp.fy)
    old, new = calc_regime(inp, cfg, "old"), calc_regime(inp, cfg, "new")
    rec = "old" if old["total_tax"] < new["total_tax"] else "new"   # tie -> new (simpler, no proofs needed)
    return {"fy": inp.fy, "old": old, "new": new, "recommended": rec,
            "saving": abs(old["total_tax"] - new["total_tax"])}
