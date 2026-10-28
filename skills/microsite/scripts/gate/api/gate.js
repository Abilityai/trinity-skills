import { PAGE, sql, init, visitor, body, context, makeGateCookie, gateEmail } from './_lib.js';

export default async function handler(req, res) {
  if (req.method === 'GET') return res.status(200).json({ known: !!gateEmail(req) });
  if (req.method !== 'POST') return res.status(405).end();
  const b = body(req);
  const email = String(b.email || '').trim().toLowerCase();
  if (email.length > 200 || !/^[^\s@]+@[^\s@]+\.[a-z]{2,}$/.test(email)) {
    return res.status(400).json({ error: 'Enter a valid email address.' });
  }
  const vid = visitor(req, res);
  const c = context(req, b);
  await init();
  await sql`insert into deck_events (page, vid, sid, type, email, r, country, city, ua, ref)
    values (${PAGE}, ${vid}, ${c.sid}, 'email', ${email}, ${c.r}, ${c.country}, ${c.city}, ${c.ua}, ${c.ref})`;
  res.appendHeader('Set-Cookie', makeGateCookie(email));
  res.status(200).json({ ok: true });
}
