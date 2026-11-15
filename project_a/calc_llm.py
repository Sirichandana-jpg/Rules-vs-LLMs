import json
from common import gemini
from .common import ROOT, TaxInput

SYSTEM = "You are a meticulous Indian income-tax calculator. Use ONLY the rules provided. Do exact arithmetic."


def prompt_for(inp: TaxInput):
    rules = (ROOT / "rule_text" / f"fy{inp.fy.replace('-', '_')}.md").read_text()
    return (f"RULES:\n{rules}\n\nTAXPAYER (all amounts annual rupees):\n{json.dumps(inp.d())}\n\n"
            'Compute tax under BOTH regimes. Return JSON only: {"old":{"taxable_income":int,"total_tax":int,'
            '"trace":[{"item":str,"amount":number,"clause":"<exact [tag] text from RULES>"}]},"new":{...same...}}. '
            "Every trace line must cite a clause tag that appears in RULES.")


def calculate(inp: TaxInput, cache=False):
    r = gemini.generate(prompt_for(inp), system=SYSTEM, cache=cache)
    d = gemini.parse_json(r["text"])
    for reg in ("old", "new"):
        d[reg]["taxable_income"] = int(d[reg]["taxable_income"]); d[reg]["total_tax"] = int(d[reg]["total_tax"])
    d["recommended"] = "old" if d["old"]["total_tax"] < d["new"]["total_tax"] else "new"
    d["fy"] = inp.fy
    d["_usage"] = {"in": r["in_tokens"], "out": r["out_tokens"], "latency_s": r["latency_s"]}
    return d


def estimate_tokens(inp: TaxInput, out_tokens=700):
    """Offline estimate (chars/4) used when no API key is available. Output size is an ASSUMPTION."""
    return len(SYSTEM + prompt_for(inp)) // 4, out_tokens
