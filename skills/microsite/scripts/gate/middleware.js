// Email gate for a private microsite share. Runs before every static file:
// without a valid signed cookie the visitor gets the gate page, never the page itself.
export const config = { matcher: ['/((?!api/).*)'] };

const enc = new TextEncoder();

function b64url(bytes) {
  let s = '';
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function valid(cookie) {
  const secret = process.env.GATE_SECRET;
  if (!secret || !cookie) return false;
  const parts = cookie.split('.');
  if (parts.length !== 3) return false;
  const [mail, exp, sig] = parts;
  if (!(Number(exp) > Date.now())) return false;
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const mac = await crypto.subtle.sign('HMAC', key, enc.encode(mail + '.' + exp));
  return b64url(new Uint8Array(mac)) === sig;
}

export default async function middleware(request) {
  const m = /(?:^|;\s*)ms_g=([^;]+)/.exec(request.headers.get('cookie') || '');
  if (await valid(m && m[1])) {
    return new Response(null, { headers: { 'x-middleware-next': '1' } });
  }
  const url = new URL(request.url);
  if (/\.[a-z0-9]+$/i.test(url.pathname) && !/\.html?$/i.test(url.pathname)) {
    return new Response('Not available', { status: 401 });
  }
  return new Response(null, {
    headers: { 'x-middleware-rewrite': new URL('/_gate.html', request.url).toString() },
  });
}
