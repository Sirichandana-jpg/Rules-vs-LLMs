"""Task 3: free text (English/Hinglish) -> TaxInput, or clarifying questions. Never guesses a missing/ambiguous fact.
parse() is rule-based (deterministic, free). llm_parse() asks Gemini for raw mentions, then runs the SAME validation
(`finalize`), so an LLM can never silently fill a gap."""
import re
from decimal import Decimal
from .common import TaxInput

WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
         "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}
MULT = {"lakh": 10**5, "lakhs": 10**5, "lac": 10**5, "lacs": 10**5, "lpa": 10**5, "l": 10**5, "crore": 10**7, "crores": 10**7, "cr": 10**7,
        "k": 1000, "thousand": 1000, "hazaar": 1000, "hazar": 1000, "hajar": 1000}
NUM = re.compile(r"(\d+(?:\.\d+)?)\s*(lakhs?|lacs?|lpa|crores?|cr|k|thousand|hazaar|hazar|hajar|l)?\b", re.I)
MONTHLY = re.compile(r"per\s*month|monthly|a\s*month|/\s*month|/\s*mo\b|mahine|mahina|\bpm\b|p\.m\.", re.I)
ANNUAL = re.compile(r"per\s*annum|annual|annually|a\s*year|yearly|per\s*year|/\s*year|\blpa\b|saal\s*ka|\bp\.?a\.?\b|salana", re.I)
FIELDS = [
    ("hli", r"(home|house|housing|ghar)\W+(?:\w+\W+){0,2}loan|loan\W+(?:\w+\W+){0,2}interest|24\(b\)"),
    ("nps", r"\bnps\b|80ccd"),
    ("inv80c", r"80c\b|\bppf\b|\belss\b|\blic\b|\bepf\b|\bvpf\b|\bnsc\b|tax saver|life insurance|\bulip\b|sukanya|tuition"),
    ("health_self", r"insur|mediclaim|health|80d|medical"),
    ("rent", r"\brent|kiraya|kiraye"),
    ("hra", r"\bhra\b|house rent allowance"),
    ("basic", r"\bbasic\b"),
    ("salary", r"salary|\bsal\b|income|earn|\bmake\b|\bmakes\b|package|\blpa\b|kama|tankhwah|pagar|gross|wage|ctc|take.?home|in.?hand"),
]
FIELDS = [(f, re.compile(r, re.I)) for f, r in FIELDS]
PARENT = re.compile(r"parent|mother|father|\bmaa\b|papa|mummy|\bmom\b|\bdad\b", re.I)
INSUR = re.compile(r"insur|mediclaim|health|medical", re.I)
METRO = {"delhi", "new delhi", "mumbai", "bombay", "kolkata", "calcutta", "chennai", "madras"}
NONMETRO = {"bangalore", "bengaluru", "pune", "hyderabad", "ahmedabad", "gurgaon", "gurugram", "noida", "jaipur", "lucknow", "kochi", "indore",
            "nagpur", "surat", "chandigarh", "bhopal", "patna", "coimbatore", "thane", "navi mumbai"}
Q = {"salary": "What is your total annual gross salary (before tax)?",
     "age": "What is your age (needed for the 60+/80+ slabs and 80D limits)?",
     "salary_period": "Is that salary per month or per year?",
     "salary_unit": "Please give the salary with units (e.g. 12 lakh, or 1,200,000 rupees) and say if it is monthly or annual.",
     "salary_basis": "Is that your gross salary? CTC / take-home are not the same as gross taxable salary - please share the gross figure.",
     "basic": "What is your annual basic salary (+DA)? Needed for the HRA exemption.",
     "hra_received": "How much HRA do you receive per year?",
     "metro": "Which city do you live in? (Delhi/Mumbai/Kolkata/Chennai get the 50% HRA rule; others 40%.)",
     "rent_period": "Is the rent per month or per year?", "basic_period": "Is the basic/HRA amount per month or per year?"}


def _norm(t):
    t = t.lower().replace("₹", " ")
    t = re.sub(r"\brs\.?\s*", " ", t)
    t = re.sub(r"(?<=\d),(?=\d)", "", t)
    t = re.sub(r"\b(" + "|".join(WORDS) + r")\s+(?=lakhs?|lacs?|crores?|thousand|hazaar)", lambda m: f"{WORDS[m.group(1)]} ", t)
    return t.replace("(", ",").replace(")", ",")


def _money(m):
    u = (m.group(2) or "").lower()
    return int(Decimal(m.group(1)) * MULT.get(u, 1)), bool(u)


def _is_age(clause, m):
    before, after = clause[:m.start()], clause[m.end():]
    if m.group(2):
        return False
    return bool(re.match(r"\s*(years?|yrs?|yo|y/o|saal|year-old|age)\b", after) or
                re.search(r"\b(age|aged|umar|umr|i am|i'm|im|main)\W*(is|of|hai)?\W*$", before))


def extract(text):
    """Raw mentions -> dict field -> list of dict(value, unit, period, flags)."""
    t = _norm(text)
    fy = None
    m = re.search(r"(?:fy|f\.y\.|financial year)\s*(?:20)?(\d{2})\s*[-–/]\s*(?:20)?(\d{2})", t)
    if m: fy = f"20{m.group(1)}-{m.group(2)}"
    m = re.search(r"\bay\s*(?:20)?(\d{2})\s*[-–/]\s*(?:20)?(\d{2})", t)
    if m: fy = f"20{int(m.group(1)) - 1}-{m.group(1)}"
    t = re.sub(r"(?:fy|f\.y\.|financial year|\bay)\s*(?:20)?\d{2}\s*[-–/]\s*(?:20)?\d{2}", " ", t)
    out, flags = {}, {"senior": False, "super": False, "parents_senior": False, "city": None, "ctc": False, "inhand": False}
    flags["senior"] = bool(re.search(r"senior citizen|senior|retired|pensioner", t))
    flags["super"] = bool(re.search(r"super senior|very senior|80\+|80 plus", t))
    for city in sorted(METRO | NONMETRO, key=len, reverse=True):
        if re.search(rf"\b{city}\b", t): flags["city"] = city; break
    clauses = [c.strip() for c in re.split(r"[;\n,]|\.\s|\s+(?:and|aur|but|also|&)\s+", t) if c.strip()]
    last = None
    for c in clauses:
        parent_clause = bool(PARENT.search(c))
        if parent_clause and not INSUR.search(c):
            if re.search(r"senior", c) or any(int(x) >= 60 for x in re.findall(r"\b(\d{2})\b", c)):
                flags["parents_senior"] = True
            if not NUM.search(c) or not re.search(r"\b(80d|premium)\b", c): continue
        hits = [(f, mm.start(), mm.end()) for f, rx in FIELDS for mm in rx.finditer(c)]
        for m in NUM.finditer(c):
            val, unit = _money(m)
            if _is_age(c, m):
                out.setdefault("age", []).append({"value": val}); last = "age"; continue
            if re.match(r"\s*(years?|yrs?|saal|%)", c[m.end():]): continue
            if hits:
                f = min(hits, key=lambda h: (max(h[1] - m.end(), m.start() - h[2], 0), h[1] > m.start()))[0]
            elif unit or MONTHLY.search(c) or ANNUAL.search(c):
                f = "salary" if last in (None, "age") else last
            else:
                f = last or "salary"
            if f == "health_self" and parent_clause: f = "health_parents"
            if re.search(r"\bctc\b", c) and f == "salary": flags["ctc"] = True
            if re.search(r"take.?home|in.?hand|\bnet\b", c) and f == "salary": flags["inhand"] = True
            period = "m" if MONTHLY.search(c) else ("a" if ANNUAL.search(c) or re.search(r"\blpa\b", c) else None)
            out.setdefault(f, []).append({"value": val, "unit": unit, "period": period})
            last = f
    if re.search(r"\blpa\b", t):
        for e in out.get("salary", []): e["period"] = "a"
    return fy, out, flags


def finalize(fy, out, flags, default_fy="2024-25"):
    q, assume, kw = [], [], {}
    ask = lambda f: q.append({"field": f, "question": Q[f]}) if all(x["field"] != f for x in q) else None
    # age
    ages = sorted({e["value"] for e in out.get("age", [])})
    if len(ages) > 1: ask("age")
    elif ages: kw["age"] = ages[0]
    elif flags["super"]: kw["age"] = 82; assume.append("super senior citizen => age band 80+")
    elif flags["senior"]: kw["age"] = 60; assume.append("senior citizen => age band 60-79")
    else: ask("age")
    # salary
    sal = out.get("salary", [])
    if not sal: ask("salary")
    elif flags["ctc"] or flags["inhand"]: ask("salary_basis")
    else:
        vals = set()
        for e in sal:
            v = e["value"]
            if not e["unit"] and v < 1000: ask("salary_unit"); continue
            if e["period"] == "m": v *= 12
            elif e["period"] is None and v < 300000: ask("salary_period"); continue
            vals.add(v)
        if len(vals) > 1: ask("salary")
        elif vals and not (flags["ctc"] or flags["inhand"]): kw["gross_salary"] = vals.pop()
        elif vals: ask("salary_basis")
    def amt(field, qf):
        es = out.get(field, [])
        if not es: return None
        vs = set()
        for e in es:
            v = e["value"]
            if e["period"] == "m": v *= 12
            elif e["period"] is None and field == "rent" and v < 200000: ask(qf); return None
            elif e["period"] is None and field in ("basic", "hra"):
                g = kw.get("gross_salary")
                if not (g and v <= g < v * 12): ask(qf); return None
            vs.add(v)
        return vs.pop() if len(vs) == 1 else (ask(qf) or None)
    if "rent" in out:
        r = amt("rent", "rent_period")
        if r is not None: kw["rent_paid"] = r
        b, h = amt("basic", "basic_period") if "basic" in out else None, amt("hra", "basic_period") if "hra" in out else None
        if b is None and "basic" not in out: ask("basic")
        if h is None and "hra" not in out: ask("hra_received")
        if b is not None: kw["basic"] = b
        if h is not None: kw["hra_received"] = h
        c = flags["city"]
        if c in METRO: kw["metro"] = True
        elif c in NONMETRO: kw["metro"] = False
        else: ask("metro")
    else:
        for f, k in (("basic", "basic"), ("hra", "hra_received")):
            v = amt(f, "basic_period")
            if v is not None: kw[k] = v
    for f, k in (("inv80c", "inv_80c"), ("nps", "nps_80ccd1b"), ("health_self", "health_self"), ("health_parents", "health_parents"), ("hli", "home_loan_interest")):
        if f in out: kw[k] = sum(e["value"] * (12 if e["period"] == "m" else 1) for e in out[f])
    if flags["parents_senior"]: kw["parents_senior"] = True
    kw["fy"] = fy or default_fy
    if not fy: assume.append(f"financial year not stated => {default_fy}")
    for f in ("inv80c", "nps", "health_self", "hli"):
        if f not in out: assume.append(f"no {f} mentioned => 0"); 
    return {"status": "needs_clarification" if q else "ok", "input": kw, "questions": q, "assumptions": assume}


def parse(text, default_fy="2024-25"):
    return finalize(*extract(text), default_fy=default_fy)


def to_taxinput(res):
    if res["status"] != "ok": raise ValueError("clarification needed: " + "; ".join(x["question"] for x in res["questions"]))
    return TaxInput(**res["input"])


def llm_parse(text, default_fy="2024-25"):
    """LLM extracts mentions; validation is identical to the rule parser. Requires GEMINI_API_KEY."""
    from common import gemini
    p = ("Extract salary-tax facts from the user text (English/Hinglish). Return JSON: {\"fy\":null|\"2025-26\",\"mentions\":"
         "[{\"field\":\"salary|age|basic|hra|rent|inv80c|nps|health_self|health_parents|hli\",\"value\":<number in rupees or years>,"
         "\"period\":\"m|a|null\",\"explicit_unit\":bool}],\"flags\":{\"ctc\":bool,\"inhand\":bool,\"city\":null|string,\"parents_senior\":bool,\"senior\":bool,\"super\":bool}}. "
         "Copy numbers exactly as stated; NEVER infer missing values. Text: " + text)
    d = gemini.parse_json(gemini.generate(p)["text"])
    out = {}
    for m in d["mentions"]:
        out.setdefault(m["field"], []).append({"value": int(m["value"]), "unit": m.get("explicit_unit", True), "period": None if m.get("period") in (None, "null") else m["period"]})
    fl = {"senior": False, "super": False, "parents_senior": False, "city": None, "ctc": False, "inhand": False}; fl.update(d.get("flags", {}))
    return finalize(d.get("fy"), out, fl, default_fy)
