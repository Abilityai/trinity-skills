# Email gate + view tracking kit

Staged into a Vercel deploy by `../share_vercel.py --gate` (and `--gate --soft`).
Never deployed on its own.

| File | Role |
|---|---|
| `middleware.js` | Hard gate only: serves `_gate.html` until a signed cookie is present |
| `gate.html` | The email form (`__TITLE__` / `__HEAD__` / `__TAG__` filled at staging) |
| `tracker.js` | First-party tracker injected before `</body>`: section dwell, clicks, `?r=` tag |
| `ask.js` | Soft mode only: the dismissible email card after ~45 active seconds |
| `api/gate.js` | Accepts the email, sets the signed cookie |
| `api/t.js` | Event sink for the tracker |
| `api/report.js` | Read-only JSON report, `Authorization: Bearer $GATE_REPORT_TOKEN` |
| `api/_lib.js` | Shared Postgres client; creates the one `deck_events` table on first write |

Environment on each gated Vercel project, set by `share_vercel.py` on first gating and
reused by every redeploy (these live on the Vercel project, not in the agent):

GATE_SECRET=<generated per project, signs the cookie>
GATE_PAGE=<the project name, tags this page's events>

The other two come from the agent's environment (or `~/.config/microsite/gate.env`):
`GATE_DATABASE_URL` (any Postgres connection string; one database for all gated pages)
and `GATE_REPORT_TOKEN` (any long random string you keep, to read `/api/report`).
