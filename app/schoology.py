import os, time, logging
from urllib.parse import urljoin
import requests
from requests_oauthlib import OAuth1

log = logging.getLogger("schoology")
API_BASE = "https://api.schoology.com"
MAX_REDIRECTS = 5

def classify(s):
    if s is None: return "CONNECTION ERROR"
    if 200 <= s < 300: return "SUCCESS"
    if 300 <= s < 400: return "REDIRECT"
    return {401: "AUTHENTICATION ERROR", 403: "FORBIDDEN / NOT AUTHORIZED",
            404: "NOT FOUND", 429: "RATE LIMITED"}.get(s, "SCHOOLOGY SERVER ERROR" if s >= 500 else "CLIENT ERROR")

def build_url(path):
    """Only ever returns https://api.schoology.com/v1/... URLs."""
    if path.startswith(API_BASE):
        path = path[len(API_BASE):]
    if not path.startswith("/v1/") or ".." in path or "@" in path or "\\" in path or " " in path:
        raise ValueError("Only /v1/... Schoology API paths are allowed")
    return API_BASE + path

def _auth():
    k, s = os.getenv("SCHOOLOGY_CONSUMER_KEY"), os.getenv("SCHOOLOGY_CONSUMER_SECRET")
    if not k or not s:
        raise RuntimeError("Missing SCHOOLOGY_CONSUMER_KEY / SCHOOLOGY_CONSUMER_SECRET in .env")
    return OAuth1(k, client_secret=s, signature_type="auth_header")  # fresh nonce/timestamp per use

def get(path):
    """Signed GET; follows redirects manually, re-signing every hop."""
    start, url, hops = time.time(), build_url(path), 0
    out = {"status": None, "classification": None, "final_url": url, "redirect_count": 0,
           "redirects": [], "body": None, "is_json": False, "error": None, "elapsed_ms": 0}
    try:
        while True:
            r = requests.get(url, auth=_auth(), allow_redirects=False, timeout=15,
                             headers={"Accept": "application/json"})
            if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("Location"):
                nxt = urljoin(url, r.headers["Location"])
                log.info("GET %s %s redirecting", url, r.status_code)
                hops += 1
                out["redirects"].append({"status": r.status_code, "to": nxt})
                if hops > MAX_REDIRECTS: raise RuntimeError("Too many redirects")
                url = build_url(nxt)  # rejects redirects leaving the API host
                continue
            out.update(status=r.status_code, final_url=url, redirect_count=hops)
            try:
                out["body"], out["is_json"] = r.json(), True
            except ValueError:
                out["body"] = r.text or None
                if not r.text: out["error"] = "Empty response"
            break
    except requests.Timeout:
        out["error"] = "Request timed out"
    except requests.ConnectionError as e:
        out["error"] = "Connection error: " + type(e).__name__
    except (ValueError, RuntimeError) as e:
        out["error"] = str(e)
    out["elapsed_ms"] = int((time.time() - start) * 1000)
    out["classification"] = classify(out["status"])
    log.info("GET %s %s %sms", out["final_url"], out["status"], out["elapsed_ms"])
    return out
