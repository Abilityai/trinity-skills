---
name: subscribe
description: Connect a resident Architect (agent-builder on a customer instance, a Regent on the control plane) to the hosted Architect — print the exact register_a2a_endpoint call an admin runs (admin and human-only; an agent key is refused), verify the registered endpoint by name with one probe call once ARCHITECT_ADVISOR is set, and record the subscription state. Never registers an endpoint itself, never stores a credential, never quotes a price.
category: agent-development
user-invocable: true
argument-hint: "[--verify] [--url <agent-card-url>] [--name <endpoint-name>]"
when_to_use: When a person wants this agent connected to the hosted Architect (cornelius-architect) for fleet designs and proposals grounded in doctrine — "subscribe to the Architect", "connect the advisor", "verify the hosted endpoint" — or after an admin registered the endpoint and set ARCHITECT_ADVISOR. Not for registering the endpoint itself (admin and human-only) and not for buying the plan (the paid door).
allowed-tools: Read, Write, Bash, Glob, Grep, mcp__trinity__call_a2a_agent, mcp__trinity__get_a2a_task, mcp__trinity__ask_operator, mcp__trinity__get_my_ask, mcp__trinity__report
requires:
  env: [ARCHITECT_ADVISOR]
metadata:
  version: "1.2"
  created: 2026-10-28
  author: trinity-pm
  changelog:
    - "1.2: moved into the library set `architect` (trinity-enterprise#987, 2026-10-29) so every resident — agent-builder and the Regents — gets the door to the hosted Architect; the agent-builder repo-native copy is retired"
    - "1.1: folded into agent-builder from the retired Abilityai/architect template (trinity-enterprise#996, 2026-10-29): same door, this agent is the resident"
    - "1.0: Initial version — the subscription door for the resident Architect (rulings 8/9 of trinity-enterprise#988): registration is a person's act (register_a2a_endpoint is admin + human-only), so the skill prints the exact call with auth_scheme aauth, raises one ask carrying it, and --verify probes the endpoint named by ARCHITECT_ADVISOR with call_a2a_agent, reading endpoint_not_found / payment_required / working honestly; state/subscription.json"
---

# Subscribe

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `subscribe vX.Y — recent: <summary>`. Then proceed.

## Purpose

Unsubscribed, this agent is complete: it builds agents from the wizard and, with the `architect` library set assigned, checks the fleet against a view a person wrote. Subscribed, it also reaches the **hosted Architect** (`cornelius-architect`) — where doctrine lives — for the founding design (`/design-fleet`), re-design proposals (`/propose-view`) and one agent's design (`/design-agent`), all over Trinity's outbound A2A door. The door has three parts, and this skill owns the honest half of each: the **endpoint** (registered by an admin, a person — this skill prepares the call and verifies the result), the **identity** (`auth_scheme: aauth` — each call is signed as this agent, `aauth:<agent>@<this host>`, no stored credential), and the **plan** (subscription, or per design — set on the paid door, never here).

## Rules this skill encodes

- **Registration is a person's act.** `register_a2a_endpoint` and `list_a2a_endpoints` refuse every agent-scoped key — the outbound registry is platform-wide, so a write grants a credentialed egress target to every agent on the instance (Invariant #8). This skill never attempts them; it prints the call and raises one ask.
- **No credential, no price.** With `auth_scheme: aauth` the endpoint stores no secret (the store refuses one). Pricing words are "subscription or per design"; figures are the paid door's.
- **One probe, never re-sent.** `--verify` makes one `call_a2a_agent` with a stable `dedup_label`; `working` is polled, never re-sent; a `payment_required` outcome is reported as the state of the plan, not retried.
- **Evidence may flow upward (ruling 9).** Subscribing means this fleet's view, gap digest and outcome deltas may be sent with `/propose-view` and may feed doctrine; the ask says so in plain words, and `state/subscription.json` records that it was said.

## Process

### Step 1: State

Read `state/subscription.json` if present (`{endpoint_name, agent_card_url, registered_asked_at, request_id, verified_at, last_probe, upward_consent_stated}`). Read `ARCHITECT_ADVISOR` from the environment or `.env`.

### Step 2: Prepare the registration (no `--verify`, or `ARCHITECT_ADVISOR` empty)

Resolve `<name>` (`--name`, else `hosted-architect`) and `<url>` (`--url`, else the Agent Card URL the person gives; **none known → stop and ask for it in the reply** — never a plausible URL). Print the exact call for an admin, in a person's session (the Trinity UI's A2A tab, or an MCP client with a human admin key):

```
register_a2a_endpoint(name="<name>", url="<url>", auth_scheme="aauth")
# then, once: set a2a_outbound_enabled (PUT /api/settings/a2a_outbound_enabled) or A2A_OUTBOUND_ENABLED=true
# then set ARCHITECT_ADVISOR=<name> in this agent's Settings → Credentials
```

Also print what the peer must do: list this agent's AAuth identity `aauth:<agent>@<this host>` in its inbound allow-list — the hosted Architect's operator does that when the plan is bought.

Raise **one** ask (`get_my_ask` first; `pending` → say it waits, stop): `ask_operator(request_id="subscribe:<name>", type="approval", to="primary", priority="medium", title="Register the hosted Architect endpoint (<name>)", question="<the three lines above, plus: subscribing means this fleet's view, gap digest and outcomes may be sent to the hosted Architect and may feed its doctrine>", options=["I registered it and set ARCHITECT_ADVISOR", "Not now"])`. Record `registered_asked_at`, `request_id`, `upward_consent_stated: true`. End the turn.

### Step 3: Verify (`--verify`, or on resume when the ask is answered approving)

`ARCHITECT_ADVISOR` must be set; otherwise print `ARCHITECT_ADVISOR is empty — set it to the endpoint name and re-run` and stop. One probe:

```
mcp__trinity__call_a2a_agent(agent_name="<self>", endpoint="${ARCHITECT_ADVISOR}",
  message="/design-fleet", dedup_label="subscribe-probe-<date>")
```

`/design-fleet` with no brief is answered with exactly one `ASK:` line and no view (canon `protocols/agent-design.md` › The one ask) — the cheapest honest round trip. Read the outcome:

| outcome | meaning | record |
|---|---|---|
| a reply starting `ASK:` | connected, identity accepted, plan in force | `verified_at`, `last_probe: ok` |
| `working` / `submitted` + `task_id` | the remote accepted; poll `get_a2a_task` up to 2 min; never re-send | per the final state |
| `endpoint_not_found` | not registered under that name on this instance | `last_probe: endpoint_not_found` — print Step 2's call again |
| outbound disabled hint | `a2a_outbound_enabled` is off — one admin step | `last_probe: outbound_off` |
| `payment_required` | registered and reachable; no plan in force for this agent — a person buys it on the paid door | `last_probe: payment_required` — say "subscription or per design", no figure |
| identity refused by the peer | the hosted side has not listed `aauth:<agent>@<host>` yet | `last_probe: identity_not_listed` |

Write `state/subscription.json`. Print one line: `subscribe: <name> — <outcome>`.

### Step 4: Report

**Only when `mcp__trinity__report` is available**: `report_type: architect.subscription`, `title: Subscription <name>: <outcome>`, `display_hint: markdown`, payload `{markdown: "<name> · <url or unknown> · <outcome> · upward consent stated <yes/no> · <date>"}`. Skip silently when absent.

## Outputs

- The exact registration call, printed for an admin; one ask carrying it
- `state/subscription.json` (gitignored)
- `architect.subscription` report when available
- Nothing registered, nothing stored, nothing priced by this agent

## Error recovery

| Situation | Action |
|---|---|
| No Agent Card URL known | Stop; ask for it in the reply — never invent one |
| `ask_operator` → `409 already_pending` | Read the named ask; say it waits; stop |
| `call_a2a_agent` refused with a 403 on the agent key | Report verbatim; the outbound door is admin-configured — a person's step |
| Probe times out | Record `last_probe: timeout`; never re-send; a person re-runs `--verify` |
