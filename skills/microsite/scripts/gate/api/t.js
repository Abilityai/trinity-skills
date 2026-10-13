import { PAGE, sql, init, visitor, body, context, gateEmail, cut } from './_lib.js';

const TYPES = new Set(['gate_view', 'open', 'dwell']);

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();
  const b = body(req);
  const type = TYPES.has(b.type) ? b.type : 'dwell';
  const vid = visitor(req, res);
  const email = gateEmail(req);
  const c = context(req, b);
  const rows = [];
  if (type !== 'dwell') rows.push({ type, section: null, secs: null, data: { vw: Number(b.vw) || null } });
  for (const it of Array.isArray(b.items) ? b.items.slice(0, 40) : []) {
    const secs = Math.min(Math.max(Math.round(Number(it && it.secs) || 0), 0), 60);
    const section = cut(it && it.section, 60);
    if (secs && section) rows.push({ type: 'dwell', section, secs, data: null });
  }
  for (const href of Array.isArray(b.clicks) ? b.clicks.slice(0, 10) : []) {
    if (cut(href, 400)) rows.push({ type: 'click', section: cut(b.at, 60), secs: null, data: { href: cut(href, 400) } });
  }
  if (rows.length) {
    await init();
    await Promise.all(rows.map((r) => sql`insert into deck_events
      (page, vid, sid, type, section, secs, email, r, country, city, ua, ref, data)
      values (${PAGE}, ${vid}, ${c.sid}, ${r.type}, ${r.section}, ${r.secs}, ${email}, ${c.r},
              ${c.country}, ${c.city}, ${c.ua}, ${c.ref}, ${r.data ? JSON.stringify(r.data) : null})`));
  }
  res.status(204).end();
}
