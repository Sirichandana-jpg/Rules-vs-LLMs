"""Shared types/helpers for Project A. Money is exact (Fraction); results are whole rupees."""
import json, re
from dataclasses import dataclass, asdict
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).parent
SUPPORTED_FY = ("2024-25", "2025-26")


@dataclass
class TaxInput:
    fy: str = "2024-25"
    age: int = 30
    gross_salary: int = 0          # annual gross salary (Sec 17(1) salary incl. HRA), rupees
    basic: int = 0                 # annual basic + DA (for HRA)
    hra_received: int = 0          # annual HRA received
    rent_paid: int = 0             # annual rent paid
    metro: bool = False            # Delhi/Mumbai/Kolkata/Chennai (50% rule)
    inv_80c: int = 0
    nps_80ccd1b: int = 0
    health_self: int = 0           # 80D premium: self/spouse/children
    health_parents: int = 0        # 80D premium: parents
    parents_senior: bool = False
    home_loan_interest: int = 0    # self-occupied, Sec 24(b)

    def d(self):
        return asdict(self)


def round10(x):
    """Sec 288A/288B: ignore fraction of a rupee, then round to nearest multiple of 10 (5 rounds up)."""
    n = int(F(x) // 1)
    return ((n + 5) // 10) * 10


def slab_tax(x, slabs):
    """slabs = [[upper_limit|None, rate_pct], ...] cumulative upper limits."""
    tax, lo = F(0), 0
    for up, rate in slabs:
        hi = x if up is None else min(x, up)
        if hi > lo:
            tax += (hi - lo) * F(rate, 100)
        if up is None or x <= up:
            break
        lo = up
    return tax


def sur_rate(x, tiers):
    """Surcharge % applicable to income x: highest tier whose threshold is strictly below x."""
    r = 0
    for t, p in tiers:
        if x > t:
            r = p
    return r


def thresh(x, tiers):
    T = 0
    for t, p in tiers:
        if x > t:
            T = t
    return T


def num(x):
    x = F(x)
    return int(x) if x.denominator == 1 else float(x)


def load_json(p):
    return json.loads(Path(p).read_text())


def clause_ids(fy):
    """Clause tags like [Sec 87A] that appear in the official-rule summary the LLM implementations read."""
    text = (ROOT / "rule_text" / f"fy{fy.replace('-', '_')}.md").read_text()
    return set(re.findall(r"\[([^\]\n]+)\]", text))


def error_str(o):
    return json.dumps(o, sort_keys=True, default=str)
