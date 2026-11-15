import argparse, io, os, time, urllib.parse, urllib.request, datetime as dt
import pandas as pd
from .schema import COLS
from .data import RAW
URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.csv"


def get(params, tries=5):
    q = URL + "?" + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            req = urllib.request.Request(q, headers={"X-App-Token": os.environ["SODA_APP_TOKEN"]} if "SODA_APP_TOKEN" in os.environ else {})
            return pd.read_csv(io.BytesIO(urllib.request.urlopen(req, timeout=120).read()), dtype=str)
        except Exception as e:
            time.sleep(3 * (i + 1)); err = e
    raise err


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--per-day", type=int, default=600); a = ap.parse_args()
    d, parts = dt.date(2023, 1, 1), []
    while d.year == 2023:
        n = d + dt.timedelta(days=1)
        p = {"$select": ",".join(COLS), "$where": f"created_date >= '{d}T00:00:00' AND created_date < '{n}T00:00:00'", "$order": "unique_key"}
        if a.per_day: p["$limit"] = a.per_day
        else: p["$limit"] = 50000
        parts.append(get(p)); d = n
        if d.day == 1: print("fetched through", d)
    RAW.parent.mkdir(exist_ok=True); pd.concat(parts).to_csv(RAW, index=False); print("wrote", RAW)


if __name__ == "__main__":
    main()
