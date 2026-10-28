import crypto from 'node:crypto';
import { neon } from '@neondatabase/serverless';

export const PAGE = process.env.GATE_PAGE || process.env.VERCEL_PROJECT_PRODUCTION_URL || 'page';
export const sql = neon(process.env.GATE_DATABASE_URL);

let ready;
export function init() {
  if (!ready) {
    ready = (async () => {
      await sql`create table if not exists deck_events (
        id bigserial primary key, ts timestamptz not null default now(),
        page text not null, vid text not null, sid text, type text not null,
        section text, secs int, email text, r text, country text, city text,
        ua text, ref text, data jsonb)`;
      await sql`create index if not exists deck_events_page_vid on deck_events (page, vid)`;
    })().catch((e) => { ready = null; throw e; });
  }
  return ready;
}

export function cookies(req) {
  const out = {};
  for (const part of (req.headers.cookie || '').split(/;\s*/)) {
    const i = part.indexOf('=');
    if (i > 0) out[part.slice(0, i)] = part.slice(i + 1);
  }
  return out;
}

const sign = (msg) => crypto.createHmac('sha256', process.env.GATE_SECRET).update(msg).digest('base64url');

export function makeGateCookie(email, days = 90) {
  const body = Buffer.from(email).toString('base64url') + '.' + (Date.now() + days * 864e5);
  return `ms_g=${body}.${sign(body)}; Path=/; Max-Age=${days * 86400}; HttpOnly; Secure; SameSite=Lax`;
}

export function gateEmail(req) {
  const c = cookies(req).ms_g;
  if (!c) return null;
  const [mail, exp, sig] = c.split('.');
  if (!sig || !(Number(exp) > Date.now())) return null;
  const want = Buffer.from(sign(mail + '.' + exp));
  const got = Buffer.from(sig);
  if (want.length !== got.length || !crypto.timingSafeEqual(want, got)) return null;
  return Buffer.from(mail, 'base64url').toString();
}

// anonymous visitor id: lives in a first-party cookie from the first tracked hit,
// so time spent before an email is known is attributable once the email arrives
export function visitor(req, res) {
  let vid = cookies(req).ms_v;
  if (!/^[a-f0-9]{24}$/.test(vid || '')) {
    vid = crypto.randomBytes(12).toString('hex');
    res.appendHeader('Set-Cookie', `ms_v=${vid}; Path=/; Max-Age=31536000; HttpOnly; Secure; SameSite=Lax`);
  }
  return vid;
}

export function body(req) {
  let b = req.body;
  if (typeof b === 'string') { try { b = JSON.parse(b); } catch { b = {}; } }
  return b && typeof b === 'object' ? b : {};
}

const cut = (v, n) => (typeof v === 'string' && v ? v.slice(0, n) : null);

export function context(req, b) {
  let city = req.headers['x-vercel-ip-city'] || null;
  try { if (city) city = decodeURIComponent(city); } catch {}
  return {
    sid: cut(b.sid, 40), r: cut(b.r, 80), ref: cut(b.ref, 300),
    country: req.headers['x-vercel-ip-country'] || null, city,
    ua: cut(req.headers['user-agent'], 300),
  };
}

export { cut };
