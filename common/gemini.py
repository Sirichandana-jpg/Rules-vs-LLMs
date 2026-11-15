import os, json, time, hashlib, urllib.request, urllib.error
from pathlib import Path

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
CACHE = Path(os.environ.get("LLM_CACHE_DIR", ".llm_cache"))


def available() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def price_per_m():
    """USD per 1M tokens (in, out) from env; None if unset. We never assume a price."""
    try:
        return float(os.environ["GEMINI_PRICE_IN_PER_M"]), float(os.environ["GEMINI_PRICE_OUT_PER_M"])
    except KeyError:
        return None


def generate(prompt, system=None, json_mode=True, cache=True, temperature=0.0, retries=5):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    h = hashlib.sha256((MODEL + (system or "") + prompt).encode()).hexdigest()
    cf = CACHE / f"{h}.json"
    if cache and cf.exists():
        d = json.loads(cf.read_text()); d["cached"] = True
        return d
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key}"
    for i in range(retries):
        t0 = time.perf_counter()
        try:
            req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.loads(r.read())
            text = resp["candidates"][0]["content"]["parts"][0]["text"]
            u = resp.get("usageMetadata", {})
            out = {"text": text, "in_tokens": u.get("promptTokenCount", 0),
                   "out_tokens": u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0),
                   "latency_s": time.perf_counter() - t0, "cached": False}
            if cache:
                CACHE.mkdir(exist_ok=True, parents=True); cf.write_text(json.dumps(out))
            return out
        except urllib.error.HTTPError as e:  # free-tier rate limits
            if e.code in (429, 500, 503):
                time.sleep(15 * (i + 1)); continue
            raise
    raise RuntimeError("Gemini: retries exhausted")


def parse_json(text):
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`").split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(t)
