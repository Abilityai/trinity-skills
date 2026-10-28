#!/usr/bin/env python3
"""Nevermined catalog client — discover, budget, and pay per call through the Router.

Stdlib only. Credentials come from the environment only: NVM_API_KEY (any
authenticated call) and NVM_DELEGATION_ID (paid calls). Discovery via `search`
and `show` is free and works without a key; only `call` spends money, and only
from a capped delegation.

  nvm.py search <text> [--category C] [--max-price 0.01] [--limit 20]
  nvm.py show <slug>                         # endpoints, prices, request schemas
  nvm.py select <intent>                     # Router picks the best payable service
  nvm.py delegation list
  nvm.py delegation create [--cents 100] [--days 7] [--tx 20]
  nvm.py delegation revoke <id>
  nvm.py call <slug> <path> [--method GET] [--query k=v ...] [--json '{..}'] [--request-id ID]
  nvm.py ledger [--request-id ID]
"""
import argparse, json, os, sys, urllib.error, urllib.parse, urllib.request, uuid
from pathlib import Path

API = "https://api.live.nevermined.app"
FEED = "https://nevermined.app/catalog/ai-catalog.json"
CACHE = Path.home() / ".cache" / "nevermined"



def key():
    k = os.environ.get("NVM_API_KEY")
    if not k:
        sys.exit("NVM_API_KEY not set — add it to this agent's credentials (a plain live: key from nevermined.app → Account → API Keys)")
    return k


def http(method, url, body=None, headers=None, auth=True):
    h = {"Accept": "application/json", "User-Agent": "trinity-nvm/0.1"}
    if auth:
        h["Authorization"] = f"Bearer {key()}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def as_json(raw):
    try:
        return json.loads(raw)
    except Exception:
        return raw.decode(errors="replace")


def out(obj):
    print(json.dumps(obj, indent=2) if not isinstance(obj, str) else obj)


def feed():
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / "ai-catalog.json"
    import time
    if not f.exists() or time.time() - f.stat().st_mtime > 3600:
        _, _, raw = http("GET", FEED, auth=False)
        f.write_bytes(raw)
    return json.loads(f.read_text())["services"]


def price(label):
    try:
        return float(str(label).lstrip("$").split()[0])
    except Exception:
        return None


def cmd_search(a):
    text = " ".join(a.text).lower()
    rows = []
    for s in feed():
        hay = " ".join([s["slug"], s["title"], s.get("description", ""), " ".join(s.get("tags", [])),
                        s.get("category", "")]).lower()
        if text and not all(w in hay for w in text.split()):
            continue
        if a.category and a.category.lower() not in s.get("category", "").lower():
            continue
        p = price(s.get("displayPriceLabel") or s.get("priceLabel"))
        if a.max_price is not None and (p is None or p > a.max_price):
            continue
        rows.append(s)
    for s in rows[: a.limit]:
        print(f"{s['slug']:<34} {s.get('displayPriceLabel') or s.get('priceLabel') or '?':>9}  "
              f"{s.get('category', ''):<26} {s['title'][:60]}")
    print(f"\n{len(rows)} match(es) of {len(feed())}")


def cmd_show(a):
    s = next((x for x in feed() if x["slug"] == a.slug), None)
    if not s:
        sys.exit(f"no catalog slug {a.slug!r}")
    # ARD search carries request schemas; the feed does not.
    _, _, raw = http("POST", f"{API}/api/v1/ard/search", {"query": {"text": s["title"]}}, auth=False)
    res = as_json(raw)
    cat = {}
    for r in (res.get("results", []) if isinstance(res, dict) else []):
        if r.get("identifier", "").endswith(":" + a.slug):
            cat = r.get("nvm:catalog", {})
            break
    print(f"{s['title']}  [{s['slug']}]  {s.get('protocol')} on {', '.join(s.get('networks', []))}")
    print(f"{s.get('description', '')}\nhealth={cat.get('healthStatus', '?')} uptime30d={cat.get('uptime30d', '?')} "
          f"payable={cat.get('routerPayable', '?')} readiness={s.get('readinessScore')}")
    for e in cat.get("endpoints") or s.get("endpoints", []):
        print(f"\n  {e['method']:<6} {e['path']}  {e.get('priceLabel', '')}  — {e.get('description', '')}")
        if e.get("requestSchema"):
            print("    schema: " + json.dumps(e["requestSchema"]))


def cmd_select(a):
    st, _, raw = http("POST", f"{API}/api/v1/router/select", {"intent": " ".join(a.intent)})
    print(st)
    out(as_json(raw))


def cmd_delegation(a):
    if a.op == "list":
        st, _, raw = http("GET", f"{API}/api/v1/delegation?accessible=true")
    elif a.op == "create":
        body = {"provider": "erc4337", "currency": "usdc", "spendingLimitCents": a.cents,
                "durationSecs": a.days * 86400, "maxTransactions": a.tx}
        st, _, raw = http("POST", f"{API}/api/v1/delegation/create", body)
    else:
        st, _, raw = http("DELETE", f"{API}/api/v1/delegation/{a.id}")
    print(st)
    out(as_json(raw))


def cmd_call(a):
    did = os.environ.get("NVM_DELEGATION_ID") or sys.exit("NVM_DELEGATION_ID not set — add a delegation id to this agent's credentials (an operator creates one with `nvm.py delegation create`)")
    rid = a.request_id or str(uuid.uuid4())
    path = a.path if a.path.startswith("/") else "/" + a.path
    q = urllib.parse.urlencode([tuple(kv.split("=", 1)) for kv in a.query]) if a.query else ""
    url = f"{API}/api/v1/router/svc/{a.slug}{path}" + (f"?{q}" if q else "")
    body = json.loads(a.json) if a.json else None
    st, hdr, raw = http(a.method, url, body,
                        {"X-Router-Delegation-Id": did, "X-Router-Request-Id": rid})
    pay = {k: v for k, v in hdr.items() if k.lower().startswith("x-router-")}
    print(f"status={st} request_id={rid}", file=sys.stderr)
    print(json.dumps(pay), file=sys.stderr)
    out(as_json(raw))
    if st >= 500 or st == 202:
        print(f"! may already have charged — check `ledger --request-id {rid}` before retrying "
              f"(retry with the same --request-id)", file=sys.stderr)


def cmd_ledger(a):
    url = f"{API}/api/v1/router/payments" + (f"?requestId={a.request_id}" if a.request_id else "")
    st, _, raw = http("GET", url)
    print(st)
    out(as_json(raw))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("search"); s.add_argument("text", nargs="*"); s.add_argument("--category")
    s.add_argument("--max-price", type=float); s.add_argument("--limit", type=int, default=25)
    s.set_defaults(f=cmd_search)
    s = sp.add_parser("show"); s.add_argument("slug"); s.set_defaults(f=cmd_show)
    s = sp.add_parser("select"); s.add_argument("intent", nargs="+"); s.set_defaults(f=cmd_select)
    s = sp.add_parser("delegation"); s.add_argument("op", choices=["list", "create", "revoke"])
    s.add_argument("id", nargs="?"); s.add_argument("--cents", type=int, default=100)
    s.add_argument("--days", type=int, default=7); s.add_argument("--tx", type=int, default=20)
    s.set_defaults(f=cmd_delegation)
    s = sp.add_parser("call"); s.add_argument("slug"); s.add_argument("path")
    s.add_argument("--method", default="GET"); s.add_argument("--query", nargs="*", default=[])
    s.add_argument("--json"); s.add_argument("--request-id"); s.set_defaults(f=cmd_call)
    s = sp.add_parser("ledger"); s.add_argument("--request-id"); s.set_defaults(f=cmd_ledger)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
