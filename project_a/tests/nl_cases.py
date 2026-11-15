"""50 plain-language descriptions (English, Hinglish, incomplete, contradictory). Gold = fields that must be extracted, or
`ask` = clarification fields that must be raised (and no guessed salary/age emitted)."""
G = [
 ("I am 34 and earn 12 lakh a year", dict(age=34, gross_salary=1200000)),
 ("Salary 18 LPA, age 29, I pay 25k per month rent in Mumbai, basic 9 lakh, HRA 3.6 lakh", dict(age=29, gross_salary=1800000, rent_paid=300000, metro=True, basic=900000, hra_received=360000)),
 ("meri salary 15 lakh hai aur meri umar 41 saal hai", dict(age=41, gross_salary=1500000)),
 ("mera mahine ka salary 1 lakh hai, age 30", dict(age=30, gross_salary=1200000)),
 ("I earn 50k", {"ask": ["salary_period", "age"]}),
 ("I earn 20 lakh", {"ask": ["age"]}),
 ("I am 35", {"ask": ["salary"]}),
 ("salary 10 lakh, 80C 1.5 lakh, age 28", dict(age=28, gross_salary=1000000, inv_80c=150000)),
 ("Senior citizen, age 62, salary 9 lakh, health insurance 50000", dict(age=62, gross_salary=900000, health_self=50000)),
 ("I'm 45, CTC is 25 lakh", {"ask": ["salary_basis"]}),
 ("age 33, in-hand salary 80k per month", {"ask": ["salary_basis"]}),
 ("My salary is 12 lakh, sorry I mean 14 lakh, age 30", {"ask": ["salary"]}),
 ("Age 38. Salary 24 LPA. Home loan interest 2 lakh. PPF 1 lakh, ELSS 50k.", dict(age=38, gross_salary=2400000, home_loan_interest=200000, inv_80c=150000)),
 ("I'm 31 yo, earning ₹1,200,000 per annum", dict(age=31, gross_salary=1200000)),
 ("Rs. 12,00,000 salary and age is 40", dict(age=40, gross_salary=1200000)),
 ("I earn 1.5 crore, 44 years old", dict(age=44, gross_salary=15000000)),
 ("super senior citizen, 82 years, salary 6 lakh", dict(age=82, gross_salary=600000)),
 ("age 27, salary 8 lakh, rent 15000 per month in Bangalore, basic 4 lakh, HRA 1.6 lakh", dict(age=27, gross_salary=800000, rent_paid=180000, metro=False, basic=400000, hra_received=160000)),
 ("age 27, salary 8 lakh, I pay rent 15000 per month", {"ask": ["basic", "hra_received", "metro"]}),
 ("Hi, how much tax do I pay?", {"ask": ["salary", "age"]}),
 ("kitna tax lagega? salary 7 lakh, 26 saal", dict(age=26, gross_salary=700000)),
 ("I make 60k a month and am 29 years old", dict(age=29, gross_salary=720000)),
 ("salary 1 lakh", {"ask": ["salary_period", "age"]}),
 ("age 50, annual salary 30 lakh, NPS 50000, parents mediclaim 25000, parents senior citizens", dict(age=50, gross_salary=3000000, nps_80ccd1b=50000, health_parents=25000, parents_senior=True)),
 ("35 years, ctc 20 lpa", {"ask": ["salary_basis"]}),
 ("gross salary 14 lakh per annum, age 37, 80C investments 1.2 lakh, health insurance for self 20000", dict(age=37, gross_salary=1400000, inv_80c=120000, health_self=20000)),
 ("meri age 33 hai, salary 11 lakh, ghar ka loan ka interest 1.8 lakh", dict(age=33, gross_salary=1100000, home_loan_interest=180000)),
 ("age 55 salary 16 lakh and 20 lakh", {"ask": ["salary"]}),
 ("I'm 30. Salary: 9,50,000", dict(age=30, gross_salary=950000)),
 ("earning 10 lpa, 25 years", dict(age=25, gross_salary=1000000)),
 ("salary 40 hazaar per month, age 24", dict(age=24, gross_salary=480000)),
 ("My age is 29 and gross salary is 45 lakh", dict(age=29, gross_salary=4500000)),
 ("I am 36 years old, salary is 75 lakh, 80C 1.5 lakh, NPS 50k, health insurance 25k", dict(age=36, gross_salary=7500000, inv_80c=150000, nps_80ccd1b=50000, health_self=25000)),
 ("age 58, salary 12 lakh, rent 30000 per month Delhi, basic 5 lakh, HRA 2.4 lakh", dict(age=58, gross_salary=1200000, rent_paid=360000, metro=True, basic=500000, hra_received=240000)),
 ("FY 2025-26: salary 13 lakh, age 30", dict(fy="2025-26", age=30, gross_salary=1300000)),
 ("earn 12 lakh", {"ask": ["age"]}),
 ("age 30", {"ask": ["salary"]}),
 ("salary 12 lakh, age 30 and 45", {"ask": ["age"]}),
 ("My basic is 6 lakh per year, HRA 3 lakh, rent 20k per month in Chennai, gross 14 lakh, age 32", dict(age=32, gross_salary=1400000, basic=600000, hra_received=300000, rent_paid=240000, metro=True)),
 ("age 61 sal 9.5 lakh", dict(age=61, gross_salary=950000)),
 ("mujhe tax batao: 14 lakh salary, 31 age", dict(age=31, gross_salary=1400000)),
 ("I earn about 1.2 cr, age 47", dict(age=47, gross_salary=12000000)),
 ("My salary is 12", {"ask": ["salary_unit", "age"]}),
 ("age 45, salary 5 lakh per month", dict(age=45, gross_salary=6000000)),
 ("29 yrs, 2.5 lakh monthly", dict(age=29, gross_salary=3000000)),
 ("salary 15 lakh, age 30, health insurance for parents 30000, parents aged 65", dict(age=30, gross_salary=1500000, health_parents=30000, parents_senior=True)),
 ("I'm 52, earning 33 lakh. Paid LIC 1 lakh and EPF 60k", dict(age=52, gross_salary=3300000, inv_80c=160000)),
 ("age 39, salary twelve lakh", dict(age=39, gross_salary=1200000)),
 ("I am 26, take home 70k", {"ask": ["salary_basis"]}),
 ("salary 20 lakh and age 31, I live in Pune rent 40k per month, basic 8 lakh, hra 3.2 lakh", dict(age=31, gross_salary=2000000, rent_paid=480000, metro=False, basic=800000, hra_received=320000)),
]
assert len(G) == 50, len(G)

ASK_KEYS = {"salary": "gross_salary", "age": "age", "basic": "basic", "hra_received": "hra_received", "metro": "metro", "rent_period": "rent_paid",
            "salary_period": "gross_salary", "salary_unit": "gross_salary", "salary_basis": "gross_salary"}


def check(text, gold, res):
    """Pass = all gold fields extracted exactly (status ok), or every expected question raised and the asked-about value NOT guessed."""
    if "ask" in gold:
        asked = {q["field"] for q in res["questions"]}
        return res["status"] == "needs_clarification" and set(gold["ask"]) <= asked and not any(ASK_KEYS[a] in res["input"] for a in gold["ask"])
    return res["status"] == "ok" and all(res["input"].get(k) == v for k, v in gold.items())
