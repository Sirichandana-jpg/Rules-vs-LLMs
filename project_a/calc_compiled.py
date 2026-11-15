from .common import *
from .dsl import Machine


def load_compiled(fy):
    p = ROOT / "compiled" / f"fy{fy.replace('-', '_')}.json"
    if not p.exists():
        raise KeyError(f"No compiled rules for FY {fy}")
    return load_json(p)


def calculate(inp: TaxInput):
    c = load_compiled(inp.fy)
    m = Machine(c["tables"])
    out = {"fy": inp.fy}
    for reg in ("old", "new"):
        env, tr = m.run(c["regimes"][reg], inp.d())
        out[reg] = {"taxable_income": int(env["ti"]), "total_tax": int(env["total"]), "trace": tr}
    out["recommended"] = "old" if out["old"]["total_tax"] < out["new"]["total_tax"] else "new"
    out["saving"] = abs(out["old"]["total_tax"] - out["new"]["total_tax"])
    return out
