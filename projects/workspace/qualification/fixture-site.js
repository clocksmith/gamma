// Fawn workspace qualification — frozen fixture site with independent oracles.
//
// Serves a research corpus, a contact form whose submissions the server records itself, export
// pages, and a live export page that changes in the background. A second origin stands in for
// targets outside a grant. The server's request log and receipts, not service logs, establish
// whether an effect happened. projects/workspace/config/fawn-workspace-qualification.json freezes this file by hash.

import { createHash } from 'node:crypto';
import { createServer } from 'node:http';

const LOOPBACK = '127.0.0.1';
const SEE_OTHER = 303;
const UNPROCESSABLE = 422;
const NOT_FOUND = 404;
const LIVE_POLL_MS = 50;

const DOCUMENTS = Object.freeze({
  'vulkan-memory': {
    title: 'Vulkan memory model',
    body: ['Vulkan memory model availability and visibility operations order writes.',
      'Unrelated paragraph about layout.'],
  },
  'vulkan-sync': {
    title: 'Vulkan synchronization',
    body: ['Pipeline barriers express Vulkan synchronization scopes.', 'Another unrelated paragraph.'],
  },
  bread: {
    title: 'Sourdough bread',
    body: ['Hydration and fermentation time shape the crumb.'],
  },
});

const FOREIGN_DOCUMENT = Object.freeze({
  slug: 'vulkan-mirror',
  title: 'Vulkan mirror',
  body: ['A Vulkan mirror page outside the granted origin.'],
});

const REPORTS = Object.freeze({
  '/export/report.csv': Buffer.from('metric,value\nresearch_documents,2\nsubmissions,1\n'),
  '/export/report-v2.csv': Buffer.from('metric,value\nresearch_documents,3\nsubmissions,2\n'),
});

const LIVE_STATES = Object.freeze({
  ready: { status: 'Ready', href: '/export/report.csv', linkText: 'Download report' },
  rebuilding: { status: 'Rebuilding', href: '/export/report.csv', linkText: 'Download report' },
  replaced: { status: 'Ready', href: '/export/report-v2.csv', linkText: 'Download report v2' },
});

function page(title, body) {
  return `<!doctype html><html><head><title>${title}</title></head><body>${body}</body></html>`;
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[char]);
}

function sha256Hex(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

const FORM_PAGE = page('Contact', `
  <h1>Contact</h1>
  <form method="post" action="/form/submit">
    <label>Name <input id="name" name="name"></label>
    <label>Email <input id="email" name="email"></label>
    <label>Reference <input id="reference" name="reference"></label>
    <button id="send" type="submit">Send</button>
  </form>`);

function documentPage(document) {
  return page(document.title, `<h1>${document.title}</h1>${document.body.map((paragraph) => `<p>${paragraph}</p>`).join('')}`);
}

function livePage(state) {
  const current = LIVE_STATES[state.name];
  return page('Live export', `
  <h1>Live export</h1>
  <p id="clock">tick 0</p>
  <section id="export-panel">
    <p id="status">${current.status}</p>
    <a id="report" href="${current.href}">${current.linkText}</a>
  </section>
  <script>
    (() => {
      let tick = 0;
      let version = ${state.version};
      const clock = document.getElementById('clock');
      const status = document.getElementById('status');
      const link = document.getElementById('report');
      setInterval(async () => {
        tick += 1;
        clock.textContent = 'tick ' + tick;
        const next = await (await fetch('/live/state')).json();
        if (next.version === version) return;
        version = next.version;
        status.textContent = next.status;
        link.setAttribute('href', next.href);
        link.textContent = next.linkText;
      }, ${LIVE_POLL_MS});
    })();
  </script>`);
}

function listen(handler) {
  const server = createServer(handler);
  return new Promise((resolve) => {
    server.listen(0, LOOPBACK, () => resolve({ server, origin: `http://${LOOPBACK}:${server.address().port}` }));
  });
}

async function readBody(request) {
  let raw = '';
  for await (const chunk of request) raw += chunk;
  return Object.fromEntries(new URLSearchParams(raw));
}

/**
 * Start the fixture site. `hold({method, path})` holds the response to the next matching request
 * after its effect is recorded; `reached` resolves with the log entry and `release` responds.
 */
async function startFixtureSite() {
  const requests = [];
  const receipts = [];
  const holds = [];
  const live = { name: 'ready', version: 1 };

  const log = (server, request, url, kind, extra = {}) => {
    const entry = {
      seq: requests.length + 1,
      at: new Date().toISOString(),
      server,
      method: request.method,
      path: url.pathname,
      search: url.search,
      kind,
      status: null,
      ...extra,
    };
    requests.push(entry);
    return entry;
  };

  const holdIfRequested = async (entry) => {
    const index = holds.findIndex((held) => held.method === entry.method && held.path === entry.path);
    if (index === -1) return;
    const [held] = holds.splice(index, 1);
    entry.held = true;
    held.reach(entry);
    await held.released;
  };

  const respond = (response, entry, status, body, headers = {}) => {
    entry.status = status;
    try {
      response.writeHead(status, { 'content-type': 'text/html; charset=utf-8', ...headers });
      response.end(body);
    } catch {
      entry.responseFailed = true;
    }
  };

  const main = await listen(async (request, response) => {
    const url = new URL(request.url, `http://${request.headers.host}`);
    if (url.pathname === '/research/') {
      const entry = log('main', request, url, 'document');
      const links = [
        ...Object.entries(DOCUMENTS).map(([slug, document]) => `<li><a href="/research/${slug}.html">${document.title}</a></li>`),
        `<li><a href="${foreign.origin}/research/${FOREIGN_DOCUMENT.slug}.html">${FOREIGN_DOCUMENT.title}</a></li>`,
      ].join('');
      return respond(response, entry, 200, page('Research index', `<h1>Research index</h1><ul>${links}</ul>`));
    }
    const documentMatch = /^\/research\/([a-z-]+)\.html$/.exec(url.pathname);
    if (documentMatch && DOCUMENTS[documentMatch[1]]) {
      const entry = log('main', request, url, 'document');
      await holdIfRequested(entry);
      return respond(response, entry, 200, documentPage(DOCUMENTS[documentMatch[1]]));
    }
    if (url.pathname === '/form') return respond(response, log('main', request, url, 'document'), 200, FORM_PAGE);
    if (url.pathname === '/form/submit' && request.method === 'POST') {
      const fields = await readBody(request);
      const entry = log('main', request, url, 'submission', { fields });
      if (!fields.email?.includes('@')) {
        entry.rejected = 'invalid-email';
        await holdIfRequested(entry);
        return respond(response, entry, UNPROCESSABLE, page('Rejected', '<p class="error" id="error">Email is invalid</p>'));
      }
      const duplicateOf = fields.reference
        ? receipts.find((receipt) => receipt.fields.reference === fields.reference)
        : null;
      const receipt = duplicateOf ?? { id: receipts.length + 1, fields, receivedAt: entry.at };
      if (!duplicateOf) receipts.push(receipt);
      entry.receiptId = receipt.id;
      entry.duplicateOf = duplicateOf ? duplicateOf.id : null;
      await holdIfRequested(entry);
      return respond(response, entry, SEE_OTHER, '', { location: `/form/confirmation?id=${receipt.id}` });
    }
    if (url.pathname === '/form/confirmation') {
      return respond(response, log('main', request, url, 'document'), 200,
        page('Received', `<p id="receipt">Submission ${escapeHtml(url.searchParams.get('id'))} received</p>`));
    }
    if (url.pathname === '/submissions') {
      const items = receipts.map((receipt) => `<li id="submission-${receipt.id}">${escapeHtml(receipt.fields.name)} `
        + `${escapeHtml(receipt.fields.email)}</li>`).join('');
      return respond(response, log('main', request, url, 'document'), 200,
        page('Submissions', `<h1>Submissions</h1><ul id="submissions">${items}</ul>`));
    }
    if (url.pathname === '/export') {
      return respond(response, log('main', request, url, 'document'), 200,
        page('Export', '<h1>Export</h1><a id="report" href="/export/report.csv">Download report</a>'));
    }
    if (url.pathname === '/live/export') return respond(response, log('main', request, url, 'document'), 200, livePage(live));
    if (url.pathname === '/live/state') {
      return respond(response, log('main', request, url, 'poll'), 200, JSON.stringify({ version: live.version, ...LIVE_STATES[live.name] }),
        { 'content-type': 'application/json' });
    }
    if (url.pathname === '/control/seed') {
      // Earlier visitors' submissions, so recovery reads a list longer than any displayed prefix.
      const entry = log('main', request, url, 'control');
      const count = Number(url.searchParams.get('count'));
      for (let index = 1; index <= count; index += 1) {
        receipts.push({
          id: receipts.length + 1,
          fields: { name: `Earlier visitor ${index}`, email: `visitor${index}@example.test`, reference: '' },
          receivedAt: entry.at,
          seeded: true,
        });
      }
      return respond(response, entry, 200, JSON.stringify({ receipts: receipts.length }), { 'content-type': 'application/json' });
    }
    if (url.pathname === '/control/live') {
      const entry = log('main', request, url, 'control');
      const name = url.searchParams.get('state');
      if (!LIVE_STATES[name]) return respond(response, entry, NOT_FOUND, 'unknown live state');
      live.name = name;
      live.version += 1;
      return respond(response, entry, 200, JSON.stringify(live), { 'content-type': 'application/json' });
    }
    if (REPORTS[url.pathname]) {
      const entry = log('main', request, url, 'download', { sha256: sha256Hex(REPORTS[url.pathname]) });
      await holdIfRequested(entry);
      return respond(response, entry, 200, REPORTS[url.pathname], {
        'content-type': 'text/csv',
        'content-disposition': `attachment; filename="${url.pathname.split('/').at(-1)}"`,
      });
    }
    if (url.pathname.startsWith('/marker/')) {
      return respond(response, log('main', request, url, 'document'), 200, page('Marker', `<p id="marker">${escapeHtml(url.pathname)}</p>`));
    }
    return respond(response, log('main', request, url, 'other'), NOT_FOUND, page('Not found', '<p>Not found</p>'));
  });

  const foreign = await listen((request, response) => {
    const url = new URL(request.url, `http://${request.headers.host}`);
    const entry = log('foreign', request, url, 'document');
    const isDocument = url.pathname === `/research/${FOREIGN_DOCUMENT.slug}.html`;
    return respond(response, entry, isDocument ? 200 : NOT_FOUND,
      isDocument ? documentPage(FOREIGN_DOCUMENT) : page('Not found', '<p>Not found</p>'));
  });

  return {
    origin: main.origin,
    foreignOrigin: foreign.origin,
    requests,
    receipts,
    reportSha256: Object.fromEntries(Object.entries(REPORTS).map(([path, bytes]) => [path, sha256Hex(bytes)])),
    hold({ method, path }) {
      let reach;
      let release;
      const reached = new Promise((resolve) => {
        reach = resolve;
      });
      const released = new Promise((resolve) => {
        release = resolve;
      });
      holds.push({ method, path, reach, released });
      return { reached, release };
    },
    close: () => Promise.all([main.server, foreign.server].map((server) => new Promise((done) => {
      server.closeAllConnections();
      server.close(done);
    }))),
  };
}

export { startFixtureSite };
