// Local stand-in for a signed-in issue tracker, used only to rehearse the authenticated
// investigation trial before a person spends sign-ins on a real site.
//
// It copies the one behaviour that makes the real case hard: a private page answers a signed-out
// visitor with "Page not found" (status 404) and a small "Sign in" link, never a redirect to a
// sign-in form. Nothing here is a claim about any real site's markup.
import { createServer } from 'node:http';
import { randomUUID } from 'node:crypto';

const escape = text => text.replace(/[&<>"]/g, value => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[value]);
const page = (title, body, signedIn) => `<!doctype html><title>${escape(title)}</title><header><a href="/">Tracker</a> `
  + `${signedIn ? '<span id="who">Signed in as investigator</span>' : '<a id="sign-in" href="/login">Sign in</a>'}</header><main>${body}</main>`;

export const STAND_IN_ISSUE_PATH = '/acme/checkout/issues/7';
const CODE = {
  '/acme/checkout/blob/main/src/cache.js': ['src/cache.js', `export const TTL_SECONDS = 900;
export function readPrice(cache, sku, now) {
  const entry = cache.get(sku);
  // Entries are kept until TTL_SECONDS pass; a price change inside that window is not seen.
  if (entry && now - entry.storedAt < TTL_SECONDS * 1000) return entry.price;
  return null;
}`],
  '/acme/checkout/blob/main/src/checkout.js': ['src/checkout.js', `import { readPrice } from './cache.js';
export async function total(cart, cache, prices, now) {
  let sum = 0;
  for (const line of cart) {
    const cached = readPrice(cache, line.sku, now);
    // A cache miss fetches one price at a time; forty lines mean forty sequential requests.
    const price = cached ?? await prices.fetch(line.sku);
    if (cached === null) cache.set(line.sku, { price, storedAt: now });
    sum += price * line.quantity;
  }
  return sum;
}`],
};

/** @returns a running stand-in with explicit controls for the trial's scripted steps. */
export async function startStandInSite() {
  const password = `stand-in-${randomUUID()}`, sessions = new Set(), logins = [], requests = [];
  const comments = [
    { by: 'mara', text: 'Tried raising TTL_SECONDS from 300 to 900 in src/cache.js last week. Median latency improved but customers now see stale prices for up to fifteen minutes.' },
    { by: 'devon', text: 'Attempted batching the price fetches in src/checkout.js on a branch; abandoned because the pricing service rejects more than ten SKUs per request.' },
  ];
  const server = createServer((req, res) => {
    const url = new URL(req.url, 'http://stand-in'), session = /(?:^|;\s*)session=([^;]+)/.exec(req.headers.cookie ?? '')?.[1];
    const signedIn = sessions.has(session);
    requests.push({ method: req.method, path: url.pathname, signedIn });
    res.setHeader('content-type', 'text/html; charset=utf-8');
    if (req.method === 'POST' && url.pathname === '/login') {
      let body = ''; req.on('data', bytes => { body += bytes; }); req.on('end', () => {
        const form = new URLSearchParams(body), accepted = form.get('password') === password;
        logins.push({ accepted });
        if (!accepted) { res.writeHead(303, { location: '/login' }); return res.end(); }
        const id = randomUUID(); sessions.add(id);
        res.writeHead(303, { location: form.get('return_to') || STAND_IN_ISSUE_PATH, 'set-cookie': `session=${id}; Max-Age=604800; Path=/; HttpOnly` }); res.end();
      }); return;
    }
    if (req.method !== 'GET') { res.statusCode = 405; return res.end(page('Method not allowed', '<h1>Read only</h1>', signedIn)); }
    if (url.pathname === '/login') {
      return res.end(page('Sign in', `<h1>Sign in</h1><form method="post" action="/login"><input type="hidden" name="return_to" value="${escape(url.searchParams.get('return_to') ?? '')}">`
        + '<label for="user">Username</label><input id="user" name="user"><label for="password">Password</label><input id="password" name="password" type="password">'
        + '<button id="go" type="submit">Sign in</button></form>', signedIn));
    }
    const privatePath = url.pathname === STAND_IN_ISSUE_PATH || Object.hasOwn(CODE, url.pathname);
    if (!privatePath || !signedIn) {
      res.statusCode = 404;
      return res.end(page('Page not found', '<h1>Page not found</h1><p>This page does not exist, or you do not have access to it.</p>', signedIn));
    }
    if (Object.hasOwn(CODE, url.pathname)) {
      const [name, source] = CODE[url.pathname];
      return res.end(page(`${name} at main · acme/checkout`, `<h1>${escape(name)}</h1><pre id="source">${escape(source)}</pre>`, true));
    }
    res.end(page('Checkout total is slow for large carts · Issue #7 · acme/checkout', `<h1>Checkout total is slow for large carts <span>#7</span></h1>
<p id="state">Open</p><p id="count">${comments.length} comments</p>
<article id="body">Carts with forty or more lines take over six seconds to total. The time is spent in
<a href="/acme/checkout/blob/main/src/checkout.js">src/checkout.js</a>, which reads prices through
<a href="/acme/checkout/blob/main/src/cache.js">src/cache.js</a>. We need totals under one second without showing stale prices.</article>
<ol id="comments">${comments.map(value => `<li><b>${escape(value.by)}</b>: ${escape(value.text)}</li>`).join('')}</ol>`, true));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  return {
    origin, issueUrl: origin + STAND_IN_ISSUE_PATH, signInUrl: `${origin}/login?return_to=${encodeURIComponent(STAND_IN_ISSUE_PATH)}`,
    password, logins, requests,
    /** The code pages the issue links to: the only pages that count as code evidence on this site. */
    codeUrls: Object.keys(CODE).map(path => origin + path),
    /** The site ends every session, as a real one does after days away or a revocation. */
    forgetSessions() { sessions.clear(); },
    /** Someone else comments while the investigation is interrupted. */
    addComment(by, text) { comments.push({ by, text }); },
    close: () => new Promise(resolve => server.close(resolve)),
  };
}
