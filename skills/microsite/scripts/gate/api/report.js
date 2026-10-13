import crypto from 'node:crypto';
import { PAGE, sql, init } from './_lib.js';

// Read-only view of the events, for the owner's report script. Bearer GATE_REPORT_TOKEN.
export default async function handler(req, res) {
  const want = Buffer.from('Bearer ' + (process.env.GATE_REPORT_TOKEN || ''));
  const got = Buffer.from(req.headers.authorization || '');
  if (!process.env.GATE_REPORT_TOKEN || want.length !== got.length || !crypto.timingSafeEqual(want, got)) {
    return res.status(401).json({ error: 'unauthorized' });
  }
  const page = req.query.page || PAGE;
  await init();
  if (req.query.pages) {
    return res.json({ pages: await sql`select page, count(*)::int as events, max(ts) as last from deck_events group by 1 order by 3 desc` });
  }
  // an email given once names every visit from that browser, before and after
  const viewers = await sql`
    with ident as (select vid, max(email) as email from deck_events where page = ${page} and email is not null group by vid),
    e as (select d.*, coalesce(i.email, d.email) as who from deck_events d left join ident i using (vid) where d.page = ${page})
    select coalesce(who, 'anon:' || vid) as viewer, who as email,
      min(ts) as first_seen, max(ts) as last_seen,
      count(distinct sid) filter (where type = 'open')::int as visits,
      count(*) filter (where type = 'gate_view')::int as gate_views,
      coalesce(sum(secs) filter (where type = 'dwell'), 0)::int as secs,
      array_remove(array_agg(distinct r), null) as tags,
      array_remove(array_agg(distinct nullif(concat_ws(', ', city, country), '')), null) as places,
      array_remove(array_agg(distinct ref), null) as referrers,
      (array_agg(ua order by ts desc))[1] as ua
    from e group by 1, 2 order by max(ts) desc`;
  const sections = await sql`
    with ident as (select vid, max(email) as email from deck_events where page = ${page} and email is not null group by vid)
    select coalesce(i.email, d.email, 'anon:' || d.vid) as viewer, d.section, sum(d.secs)::int as secs
    from deck_events d left join ident i using (vid)
    where d.page = ${page} and d.type = 'dwell' group by 1, 2`;
  const clicks = await sql`
    with ident as (select vid, max(email) as email from deck_events where page = ${page} and email is not null group by vid)
    select coalesce(i.email, d.email, 'anon:' || d.vid) as viewer, d.ts, d.section, d.data->>'href' as href
    from deck_events d left join ident i using (vid)
    where d.page = ${page} and d.type = 'click' order by d.ts`;
  res.json({ page, viewers, sections, clicks });
}
