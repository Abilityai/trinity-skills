---
name: nevermined-catalog
description: Discover and pay per call for external AI and data services from the Nevermined catalog (160+ x402/MPP services — web search, scraping, enrichment, finance, crypto, media) through the Nevermined Router, spending from a capped delegation. Use when a task needs an external service the agent holds no key for, or to explore what the catalog offers.
category: research-and-analysis
user-invocable: true
argument-hint: "search <words> | select <intent> | show <slug> | call <slug> <path> [--query k=v …] [--json '{…}'] | ledger [--request-id ID] | delegation list"
allowed-tools: Bash
requires:
  env: [NVM_API_KEY, NVM_DELEGATION_ID]
  binaries: [python3]
metadata:
  version: "1.0"
  changelog:
    - "1.0: Promoted from trinity-pm (authored 2026-10-16) — search/show/select discovery, delegation list/create/revoke, paid call via the Router path form, payment ledger; stdlib-only client"
---

# Nevermined catalog

Nevermined lists pay-per-call services that price each request on the wire (HTTP 402 — x402 or MPP). The Nevermined Router answers the 402, pays from a **delegation** (a budget with a hard cap in cents, a transaction count and an expiry), and returns the service's response. No per-service signup or key.

Client: `python3 ~/.claude/skills/nevermined-catalog/scripts/nvm.py <command>` — Python stdlib only. Live host (`api.live.nevermined.app`) only; the sandbox Router cannot pay listed services. **Payments are real: USDC on mainnet (Base, Tempo).**

## Credentials and cold start

| Key | Needed for | Without it |
|---|---|---|
| `NVM_API_KEY` | `select`, `call`, `ledger`, `delegation` | those commands exit naming the key; `search` and `show` still work |
| `NVM_DELEGATION_ID` | `call` | `call` exits naming the key |

`NVM_API_KEY` is a plain `live:` key a human creates in nevermined.app → Account → API Keys (pass the whole string, prefix included). An OAuth-minted key cannot pay through delegations (`403 BCK.OAUTH.0030`). The account's wallet must hold a USDC balance — a human tops it up in the app.

## 1. Discover (free — always first)

```bash
nvm.py search <words> [--category "Search"] [--max-price 0.01] [--limit 25]   # public feed, cached 1h in ~/.cache/nevermined
nvm.py select <plain-language intent>                                          # the Router ranks payable, healthy services
nvm.py show <slug>                                                             # endpoints, prices, request schemas, health
```

Read the endpoint's request schema in `show` before calling — a mismatched field name is a `422`. Prefer the cheapest healthy service that fits; listed prices exclude the Router's fee (2%), which comes out of the same cap.

## 2. Call (spends money)

```bash
nvm.py call <slug> <path> [--method GET|POST] [--query k=v ...] [--json '{...}'] [--request-id ID]
```

Calls `POST|GET /api/v1/router/svc/<slug>/<path>`. The response body prints to stdout; status, request id and the `X-Router-Payment-*` headers (payment id, status, tx hash, failure reason) print to stderr.

**Payment rules:**
- A new purchase gets a fresh request id (generated when `--request-id` is omitted). A **retry reuses the same `--request-id`** — the Router deduplicates on it (`409 BCK.ROUTER.0002`).
- After a `202`, a `5xx`, or any answer naming a payment id, the merchant may already have been paid: run `nvm.py ledger --request-id <id>` first. `"presence": "absent"` means nothing was recorded, so resend with the same id; present means do not resend.
- `402 BCK.ROUTER.0003` — the cap refused it. Report and stop; never create a new delegation to get past a cap.
- `412 consent_required` — the account must accept updated terms in nevermined.app (a human).
- `409 BCK.ROUTER.0014` — a raw URL was used for a listed service; address it by slug.
- A refusal that names no payment id cost nothing.

## 3. Budget

```bash
nvm.py delegation list                                   # active delegations this key can spend
nvm.py delegation create --cents 100 --days 7 --tx 20    # 1 USD cap, 7 days, 20 paid attempts
nvm.py delegation revoke <id>
nvm.py ledger [--request-id ID]                          # what was paid, with tx hashes
```

Creating or widening a delegation commits real money, so it is a human decision. In an interactive run, propose the cap and wait for approval. In an unattended run (a schedule, another agent's call), **never create a delegation**: work within `NVM_DELEGATION_ID`, and if it is missing, exhausted or expired, report that and stop. `maxTransactions` counts every paid attempt, retries included.
