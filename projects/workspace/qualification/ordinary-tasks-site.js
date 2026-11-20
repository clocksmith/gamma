// Ordinary browser task suite for Track C saved-workflow reuse benchmark.
//
// Hosts five everyday multi-step browser tasks (two form-fill, one ledger search-and-extract,
// two multi-page navigation) plus unmodified committed Simulatte Lucyd `/system-diagram` assets.

import { createServer } from 'node:http';
import { execFileSync } from 'node:child_process';
import { canonicalJson, sha256Hex } from '../src/journal.js';

const LOOPBACK = '127.0.0.1';
const SIMULATTE_COMMIT = '500167e0';

const INVOICE_LEDGER = Object.freeze([
  { id: 'INV-2041', vendor: 'Acme Cloud', status: 'Open', quarter: 'Q1', cents: 142000 },
  { id: 'INV-2042', vendor: 'Acme Cloud', status: 'Open', quarter: 'Q1', cents: 58000 },
  { id: 'INV-2043', vendor: 'Acme Cloud', status: 'Paid', quarter: 'Q1', cents: 91000 },
  { id: 'INV-2044', vendor: 'Beacon Fiber', status: 'Open', quarter: 'Q2', cents: 215000 },
  { id: 'INV-2045', vendor: 'Beacon Fiber', status: 'Open', quarter: 'Q2', cents: 85000 },
  { id: 'INV-2046', vendor: 'Beacon Fiber', status: 'Overdue', quarter: 'Q1', cents: 129000 },
  { id: 'INV-2047', vendor: 'Cedar Freight', status: 'Overdue', quarter: 'Q2', cents: 174000 },
  { id: 'INV-2048', vendor: 'Cedar Freight', status: 'Overdue', quarter: 'Q2', cents: 66000 },
  { id: 'INV-2049', vendor: 'Cedar Freight', status: 'Paid', quarter: 'Q3', cents: 112000 },
  { id: 'INV-2050', vendor: 'Delta Optics', status: 'Paid', quarter: 'Q3', cents: 310000 },
  { id: 'INV-2051', vendor: 'Delta Optics', status: 'Paid', quarter: 'Q3', cents: 95000 },
  { id: 'INV-2052', vendor: 'Delta Optics', status: 'Open', quarter: 'Q3', cents: 148000 },
]);

const RELEASE_CATALOG = Object.freeze([
  { version: 'v4.8.0', channel: 'Stable', subsystem: 'router', notes: 'Zero-downtime route table reload', commits: 19 },
  { version: 'v4.8.1', channel: 'Stable', subsystem: 'storage', notes: 'Write-ahead journal fsync batching', commits: 14 },
  { version: 'v4.8.2', channel: 'Stable', subsystem: 'auth', notes: 'Short-lived session token rotation', commits: 11 },
  { version: 'v4.6.9-lts', channel: 'LTS', subsystem: 'router', notes: 'Backported keepalive socket drain fix', commits: 7 },
  { version: 'v4.6.10-lts', channel: 'LTS', subsystem: 'storage', notes: 'Snapshot checksum verification repair', commits: 9 },
  { version: 'v4.6.11-lts', channel: 'LTS', subsystem: 'telemetry', notes: 'Bounded histogram cardinality guard', commits: 6 },
]);

const SHIPPING_RATES_CENTS = Object.freeze({
  Ground: 1200,
  'Two-day': 2800,
  Overnight: 5400,
});

const DOCK_UNIT_CENTS = 24900;

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

function formatDollars(cents) {
  return `$${(cents / 100).toFixed(2)}`;
}

function computeMatchingInvoices({ vendorQuery, status, quarter }) {
  const needle = String(vendorQuery ?? '').trim().toLowerCase();
  const rows = INVOICE_LEDGER.filter((item) => {
    const vendorOk = !needle || item.vendor.toLowerCase().includes(needle);
    const statusOk = !status || status === 'All' || item.status === status;
    const quarterOk = !quarter || quarter === 'All' || item.quarter === quarter;
    return vendorOk && statusOk && quarterOk;
  });
  const totalCents = rows.reduce((sum, item) => sum + item.cents, 0);
  return { ids: rows.map((item) => item.id), totalCents, formattedTotal: formatDollars(totalCents) };
}

function computeExpenseTier(category, amountStr) {
  const amount = Number(amountStr);
  if (!Number.isFinite(amount) || amount <= 0) return 'invalid';
  if (category === 'Hardware' || amount >= 500) return 'manager-review';
  return 'auto-eligible';
}

function computeDockQuote({ quantity, shippingTier }) {
  const qty = Number.parseInt(String(quantity ?? '0'), 10);
  const shipCents = SHIPPING_RATES_CENTS[shippingTier] ?? null;
  if (!Number.isInteger(qty) || qty < 1 || shipCents === null) return null;
  const subtotalCents = qty * DOCK_UNIT_CENTS;
  const totalCents = subtotalCents + shipCents;
  return {
    sku: 'TB4-PRO-DOCK',
    qty,
    subtotal: formatDollars(subtotalCents),
    shipping: formatDollars(shipCents),
    total: formatDollars(totalCents),
  };
}

function computeMatchingRelease({ channel, subsystem }) {
  const sub = String(subsystem ?? '').trim().toLowerCase();
  return RELEASE_CATALOG.find(
    (entry) => entry.channel === channel && sub && entry.subsystem.toLowerCase().includes(sub),
  ) ?? null;
}

function htmlShell(title, body) {
  return `<!doctype html><html><head><meta charset="utf-8"><title>${escapeHtml(title)}</title>
  <style>
    body { font: 15px/1.45 system-ui, sans-serif; max-width: 880px; margin: 28px auto; padding: 0 18px; }
    label { display: block; margin: 12px 0 6px; font-weight: 600; }
    input, select, button { font: inherit; padding: 7px 10px; margin-right: 8px; }
    nav a, .card a { display: inline-block; margin: 6px 10px 6px 0; padding: 6px 10px; border: 1px solid #888; }
    dl > div { margin: 6px 0; }
    dt { font-weight: 600; display: inline; }
    dd { display: inline; margin-left: 8px; }
    table { border-collapse: collapse; width: 100%; margin: 14px 0; }
    th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: left; }
  </style></head><body>${body}</body></html>`;
}

function renderApplicationPage(sessionId) {
  return htmlShell('Engineer Application', `
    <h1>Engineer Application</h1>
    <p id="status-banner">Complete applicant contact and work preferences, then open the review screen.</p>
    <main id="app-main" data-stage="contact"></main>
    <script>
      (() => {
        const state = {};
        const labels = {
          fullName: 'Full name',
          email: 'Email address',
          location: 'Current city',
          workMode: 'Work arrangement',
        };
        const main = document.getElementById('app-main');
        const save = () => {
          document.querySelectorAll('[data-slot]').forEach((el) => { state[el.dataset.slot] = el.value; });
        };
        function render(stage) {
          main.dataset.stage = stage;
          if (stage === 'contact') {
            main.innerHTML =
              '<label for="app-name">Full name</label>' +
              '<input id="app-name" data-slot="fullName" type="text" required>' +
              '<label for="app-email">Email address</label>' +
              '<input id="app-email" data-slot="email" type="email" required>' +
              '<p><button id="app-continue" type="button">Continue</button></p>';
            document.getElementById('app-name').value = state.fullName || '';
            document.getElementById('app-email').value = state.email || '';
            document.getElementById('app-continue').onclick = () => {
              save();
              if (!state.fullName || !state.email) return;
              render('questions');
            };
            return;
          }
          if (stage === 'questions') {
            main.innerHTML =
              '<label for="app-city">Current city</label>' +
              '<input id="app-city" data-slot="location" type="text" required>' +
              '<label for="app-mode">Work arrangement</label>' +
              '<select id="app-mode" data-slot="workMode">' +
                '<option value="Choose">Choose</option>' +
                '<option value="Remote">Remote</option>' +
                '<option value="Hybrid">Hybrid</option>' +
                '<option value="Office">Office</option>' +
              '</select>' +
              '<p><button id="app-review" type="button">Review application</button></p>';
            document.getElementById('app-city').value = state.location || '';
            document.getElementById('app-mode').value = state.workMode || 'Choose';
            document.getElementById('app-review').onclick = () => {
              save();
              if (!state.location || !state.workMode || state.workMode === 'Choose') return;
              render('review');
            };
            return;
          }
          const rows = ['fullName', 'email', 'location', 'workMode']
            .map((k) => '<div><dt>' + labels[k] + '</dt><dd>' + state[k] + '</dd></div>')
            .join('');
          main.innerHTML =
            '<h2>Review application</h2>' +
            '<dl id="review-fields">' + rows + '</dl>' +
            '<form method="post" action="/tasks/${escapeHtml(sessionId)}/submit">' +
              '<button id="final-submit" type="submit">Submit application</button>' +
            '</form>';
        }
        render('contact');
      })();
    </script>`);
}

function renderExpensePage(sessionId) {
  return htmlShell('Expense Reimbursement', `
    <h1>Expense Reimbursement</h1>
    <p>Enter reimbursement details and open the preview screen without submitting the claim.</p>
    <main id="expense-main" data-stage="entry">
      <label for="exp-employee">Employee name</label>
      <input id="exp-employee" type="text">
      <label for="exp-dept">Department</label>
      <select id="exp-dept">
        <option value="Choose">Choose</option>
        <option value="Engineering">Engineering</option>
        <option value="Operations">Operations</option>
        <option value="Finance">Finance</option>
      </select>
      <label for="exp-cat">Expense category</label>
      <select id="exp-cat">
        <option value="Choose">Choose</option>
        <option value="Travel">Travel</option>
        <option value="Software">Software</option>
        <option value="Hardware">Hardware</option>
      </select>
      <label for="exp-amount">Amount USD</label>
      <input id="exp-amount" type="text">
      <label for="exp-purpose">Business purpose</label>
      <input id="exp-purpose" type="text">
      <p><button id="exp-preview-btn" type="button">Preview reimbursement</button></p>
    </main>
    <script>
      (() => {
        document.getElementById('exp-preview-btn').onclick = () => {
          const employee = document.getElementById('exp-employee').value.trim();
          const department = document.getElementById('exp-dept').value;
          const category = document.getElementById('exp-cat').value;
          const amount = document.getElementById('exp-amount').value.trim();
          const purpose = document.getElementById('exp-purpose').value.trim();
          const num = Number(amount);
          if (!employee || department === 'Choose' || category === 'Choose' || !Number.isFinite(num) || num <= 0 || !purpose) {
            return;
          }
          const tier = (category === 'Hardware' || num >= 500) ? 'manager-review' : 'auto-eligible';
          const main = document.getElementById('expense-main');
          main.dataset.stage = 'preview';
          main.innerHTML = '<h2>Reimbursement preview</h2><dl id="expense-preview"></dl>' +
            '<form method="post" action="/tasks/${escapeHtml(sessionId)}/submit">' +
              '<button id="exp-submit" type="submit">Submit claim</button>' +
            '</form>';
          const dl = document.getElementById('expense-preview');
          for (const [k, v] of [
            ['Employee name', employee],
            ['Department', department],
            ['Expense category', category],
            ['Amount USD', amount],
            ['Business purpose', purpose],
            ['Approval tier', tier],
          ]) {
            const d = document.createElement('div');
            const dt = document.createElement('dt');
            const dd = document.createElement('dd');
            dt.textContent = k;
            dd.textContent = v;
            d.append(dt, dd);
            dl.append(d);
          }
        };
      })();
    </script>`);
}

function renderInvoicePage() {
  const rowsJson = JSON.stringify(INVOICE_LEDGER);
  return htmlShell('Accounts Payable Ledger', `
    <h1>Accounts Payable Ledger</h1>
    <section id="filter-controls">
      <label for="inv-vendor">Vendor search</label>
      <input id="inv-vendor" type="search">
      <label for="inv-status">Invoice status</label>
      <select id="inv-status">
        <option value="All">All</option>
        <option value="Open">Open</option>
        <option value="Overdue">Overdue</option>
        <option value="Paid">Paid</option>
      </select>
      <label for="inv-quarter">Billing quarter</label>
      <select id="inv-quarter">
        <option value="All">All</option>
        <option value="Q1">Q1</option>
        <option value="Q2">Q2</option>
        <option value="Q3">Q3</option>
      </select>
      <p>
        <button id="inv-apply" type="button">Apply ledger filter</button>
        <button id="inv-extract" type="button">Extract statement summary</button>
      </p>
    </section>
    <table><thead><tr><th>ID</th><th>Vendor</th><th>Status</th><th>Quarter</th><th>Amount</th></tr></thead>
      <tbody id="inv-tbody"></tbody>
    </table>
    <section id="extracted-summary" data-ready="false"></section>
    <script>
      (() => {
        const allRows = ${rowsJson};
        let filtered = [...allRows];
        const fmt = (c) => '$' + (c / 100).toFixed(2);
        const renderTable = () => {
          const tb = document.getElementById('inv-tbody');
          tb.innerHTML = '';
          for (const r of filtered) {
            const tr = document.createElement('tr');
            tr.innerHTML = '<td>' + r.id + '</td><td>' + r.vendor + '</td><td>' + r.status + '</td><td>' + r.quarter + '</td><td>' + fmt(r.cents) + '</td>';
            tb.append(tr);
          }
        };
        document.getElementById('inv-apply').onclick = () => {
          const needle = document.getElementById('inv-vendor').value.trim().toLowerCase();
          const st = document.getElementById('inv-status').value;
          const qt = document.getElementById('inv-quarter').value;
          filtered = allRows.filter((r) =>
            (!needle || r.vendor.toLowerCase().includes(needle)) &&
            (st === 'All' || r.status === st) &&
            (qt === 'All' || r.quarter === qt)
          );
          document.getElementById('extracted-summary').dataset.ready = 'false';
          document.getElementById('extracted-summary').innerHTML = '';
          renderTable();
        };
        document.getElementById('inv-extract').onclick = () => {
          const sec = document.getElementById('extracted-summary');
          const ids = filtered.map((r) => r.id);
          const total = fmt(filtered.reduce((s, r) => s + r.cents, 0));
          sec.dataset.ready = 'true';
          sec.dataset.ids = JSON.stringify(ids);
          sec.dataset.total = total;
          sec.innerHTML = '<h2>Extracted statement summary</h2>' +
            '<p id="summary-ids">Invoices: ' + ids.join(', ') + '</p>' +
            '<p id="summary-total">Subtotal: ' + total + '</p>';
        };
        renderTable();
      })();
    </script>`);
}

function renderStoreHome(sessionId) {
  return htmlShell('Hardware Catalog', `
    <h1>Enterprise Hardware Catalog</h1>
    <p>Select a product category to browse configurable hardware.</p>
    <nav>
      <a id="cat-docks" href="/tasks/${escapeHtml(sessionId)}/store/docks">Workstation Docks</a>
      <a id="cat-monitors" href="/tasks/${escapeHtml(sessionId)}/store/monitors">Studio Monitors</a>
    </nav>`);
}

function renderStoreDocks(sessionId) {
  return htmlShell('Workstation Docks', `
    <h1>Workstation Docks</h1>
    <div class="card">
      <h2>Thunderbolt 4 Pro Dock (TB4-PRO-DOCK)</h2>
      <p>Unit price: $249.00</p>
      <a id="open-tb4-quote" href="/tasks/${escapeHtml(sessionId)}/store/docks/tb4-quote">Configure Thunderbolt 4 Dock</a>
    </div>`);
}

function renderStoreQuote(sessionId, searchParams) {
  if (searchParams.get('view') === 'summary') {
    const quantity = searchParams.get('qty') ?? '';
    const zip = searchParams.get('zip') ?? '';
    const tier = searchParams.get('tier') ?? '';
    const costCenter = searchParams.get('cc') ?? '';
    const quote = computeDockQuote({ quantity, shippingTier: tier });
    if (quote && zip && costCenter) {
      return htmlShell('Shipping Quote Summary', `
        <h1>Shipping Quote Summary</h1>
        <dl id="quote-summary">
          <div><dt>SKU</dt><dd>${escapeHtml(quote.sku)}</dd></div>
          <div><dt>Quantity</dt><dd>${escapeHtml(String(quote.qty))}</dd></div>
          <div><dt>Destination ZIP</dt><dd>${escapeHtml(zip)}</dd></div>
          <div><dt>Shipping tier</dt><dd>${escapeHtml(tier)}</dd></div>
          <div><dt>Cost center</dt><dd>${escapeHtml(costCenter)}</dd></div>
          <div><dt>Total quote</dt><dd>${escapeHtml(quote.total)}</dd></div>
        </dl>
        <form method="post" action="/tasks/${escapeHtml(sessionId)}/submit">
          <button id="place-order" type="submit">Place order</button>
        </form>`);
    }
  }
  return htmlShell('Configure Thunderbolt 4 Dock', `
    <h1>Configure Thunderbolt 4 Dock</h1>
    <label for="q-qty">Quantity</label>
    <input id="q-qty" type="text">
    <label for="q-zip">Destination ZIP</label>
    <input id="q-zip" type="text">
    <label for="q-tier">Shipping tier</label>
    <select id="q-tier">
      <option value="Choose">Choose</option>
      <option value="Ground">Ground</option>
      <option value="Two-day">Two-day</option>
      <option value="Overnight">Overnight</option>
    </select>
    <label for="q-cc">Cost center</label>
    <input id="q-cc" type="text">
    <p><button id="calc-quote" type="button">Calculate shipping quote</button></p>
    <script>
      document.getElementById('calc-quote').onclick = () => {
        const qty = document.getElementById('q-qty').value.trim();
        const zip = document.getElementById('q-zip').value.trim();
        const tier = document.getElementById('q-tier').value;
        const cc = document.getElementById('q-cc').value.trim();
        if (!qty || !zip || tier === 'Choose' || !cc) return;
        const params = new URLSearchParams({ view: 'summary', qty, zip, tier, cc });
        location.href = '/tasks/${escapeHtml(sessionId)}/store/docks/tb4-quote?' + params.toString();
      };
    </script>`);
}

function renderDocsHome(sessionId) {
  return htmlShell('Platform Documentation', `
    <h1>Platform Documentation</h1>
    <p>Navigate to the release archive to inspect channel-specific subsystem changes.</p>
    <nav>
      <a id="nav-guides" href="/tasks/${escapeHtml(sessionId)}/docs/guides">Operator Guides</a>
      <a id="nav-releases" href="/tasks/${escapeHtml(sessionId)}/docs/releases">Release Notes Archive</a>
    </nav>`);
}

function renderDocsReleases(sessionId) {
  const catalogJson = JSON.stringify(RELEASE_CATALOG);
  return htmlShell('Release Notes Archive', `
    <h1>Release Notes Archive</h1>
    <label for="rel-channel">Release channel</label>
    <select id="rel-channel">
      <option value="Choose">Choose</option>
      <option value="Stable">Stable</option>
      <option value="LTS">LTS</option>
    </select>
    <label for="rel-subsystem">Subsystem keyword</label>
    <input id="rel-subsystem" type="search">
    <p><button id="rel-search" type="button">Filter release notes</button></p>
    <div id="rel-results"></div>
    <script>
      (() => {
        const catalog = ${catalogJson};
        document.getElementById('rel-search').onclick = () => {
          const ch = document.getElementById('rel-channel').value;
          const sub = document.getElementById('rel-subsystem').value.trim().toLowerCase();
          const box = document.getElementById('rel-results');
          box.innerHTML = '';
          if (ch === 'Choose' || !sub) return;
          const hit = catalog.find((r) => r.channel === ch && r.subsystem.toLowerCase().includes(sub));
          if (!hit) return;
          const params = new URLSearchParams({ version: hit.version });
          box.innerHTML = '<p>Matched: ' + hit.version + '</p>' +
            '<a id="open-release-digest" href="/tasks/${escapeHtml(sessionId)}/docs/releases/digest?' + params.toString() + '">Open release digest</a>';
        };
      })();
    </script>`);
}

function renderDocsDigest(searchParams) {
  const version = searchParams.get('version') ?? '';
  const entry = RELEASE_CATALOG.find((item) => item.version === version) ?? null;
  if (!entry) return htmlShell('Not Found', '<p>No release selected.</p>');
  return htmlShell(`Release Digest ${entry.version}`, `
    <h1>Release Digest</h1>
    <dl id="release-digest">
      <div><dt>Version</dt><dd>${escapeHtml(entry.version)}</dd></div>
      <div><dt>Channel</dt><dd>${escapeHtml(entry.channel)}</dd></div>
      <div><dt>Subsystem</dt><dd>${escapeHtml(entry.subsystem)}</dd></div>
      <div><dt>Commits</dt><dd>${escapeHtml(String(entry.commits))}</dd></div>
      <div><dt>Summary</dt><dd>${escapeHtml(entry.notes)}</dd></div>
    </dl>`);
}

export async function startOrdinaryTasksServer({ simulatteRepo }) {
  const sessions = new Map();
  const assetCache = new Map();
  const assetHashes = {};
  let rejectedWrites = 0;

  const simulatteRevision = simulatteRepo
    ? execFileSync('git', ['rev-parse', SIMULATTE_COMMIT], { cwd: simulatteRepo, encoding: 'utf8' }).trim()
    : null;

  const readSimulatteSource = (path) => execFileSync(
    'git',
    ['show', `${simulatteRevision}:${path}`],
    { cwd: simulatteRepo, maxBuffer: 20_000_000, stdio: ['ignore', 'pipe', 'ignore'] },
  );

  function expectedLucydIds(query) {
    const readJson = (p) => JSON.parse(readSimulatteSource(p));
    const manifest = readJson('public/data/system-diagram/class-library.json');
    const categories = new Map(manifest.categories.map((c) => [c.id, c.label]));
    const classes = manifest.packs.flatMap((p) => readJson(`public/data/system-diagram/${p}`).classes);
    const words = String(query ?? '').trim().toLowerCase().split(/\s+/);
    return classes
      .filter((c) => words.every((w) => `${c.id} ${c.label} ${c.description ?? ''} ${c.category} ${categories.get(c.category) ?? ''}`.toLowerCase().includes(w)))
      .map((c) => c.id)
      .sort();
  }

  const server = createServer(async (req, res) => {
    try {
      const parsed = new URL(req.url, 'http://localhost');
      const pathname = decodeURIComponent(parsed.pathname);
      if (pathname.includes('..')) {
        res.writeHead(400);
        res.end('Unsafe path');
        return;
      }

      if (pathname.startsWith('/tasks/')) {
        const parts = pathname.split('/').filter(Boolean);
        const sessionId = parts[1];
        const route = parts.slice(2).join('/');
        const session = sessions.get(sessionId);
        if (!session) {
          res.writeHead(404);
          res.end('Unknown task session');
          return;
        }
        if (req.method === 'POST' && route === 'submit') {
          for await (const _ of req) { /* drain */ }
          session.submissions += 1;
          res.writeHead(200, { 'content-type': 'text/plain' });
          res.end('Unexpected final submission');
          return;
        }
        if (req.method !== 'GET') {
          rejectedWrites += 1;
          res.writeHead(405);
          res.end('Method not allowed');
          return;
        }
        res.setHeader('content-type', 'text/html; charset=utf-8');
        if (route === 'application') { res.end(renderApplicationPage(sessionId)); return; }
        if (route === 'expense') { res.end(renderExpensePage(sessionId)); return; }
        if (route === 'invoices') { res.end(renderInvoicePage()); return; }
        if (route === 'store') { res.end(renderStoreHome(sessionId)); return; }
        if (route === 'store/docks') { res.end(renderStoreDocks(sessionId)); return; }
        if (route === 'store/docks/tb4-quote') { res.end(renderStoreQuote(sessionId, parsed.searchParams)); return; }
        if (route === 'docs') { res.end(renderDocsHome(sessionId)); return; }
        if (route === 'docs/releases') { res.end(renderDocsReleases(sessionId)); return; }
        if (route === 'docs/releases/digest') { res.end(renderDocsDigest(parsed.searchParams)); return; }
        res.writeHead(404);
        res.end('Unknown task route');
        return;
      }

      // Unmodified Simulatte committed `/system-diagram` product assets
      if (!simulatteRevision) {
        res.writeHead(404);
        res.end('Simulatte repository not configured');
        return;
      }
      if (req.method !== 'GET') {
        rejectedWrites += 1;
        res.writeHead(405);
        res.end();
        return;
      }
      const assetPath = pathname === '/system-diagram'
        ? 'public/simulatte/system-diagram/index.html'
        : `public${pathname.endsWith('/') ? `${pathname}index.html` : pathname}`;
      const cacheKey = `${simulatteRevision}:${assetPath}`;
      if (!assetCache.has(cacheKey)) {
        const bytes = readSimulatteSource(assetPath);
        assetCache.set(cacheKey, bytes);
        assetHashes[cacheKey] = sha256Hex(bytes);
      }
      const ext = assetPath.split('.').at(-1);
      const mime = ({
        js: 'application/javascript',
        css: 'text/css',
        json: 'application/json',
        html: 'text/html',
        svg: 'image/svg+xml',
      })[ext] ?? 'application/octet-stream';
      res.setHeader('content-type', mime);
      res.end(assetCache.get(cacheKey));
    } catch {
      res.writeHead(404);
      res.end('Not found');
    }
  });

  await new Promise((resolve) => server.listen(0, LOOPBACK, resolve));
  const origin = `http://${LOOPBACK}:${server.address().port}`;

  return {
    origin,
    simulatteRevision,
    assetHashes,
    getRejectedWrites: () => rejectedWrites,
    createSession(sessionId, routePath) {
      sessions.set(sessionId, { submissions: 0 });
      return routePath === '/system-diagram'
        ? `${origin}/system-diagram`
        : `${origin}/tasks/${sessionId}/${routePath}`;
    },
    getSubmissions(sessionId) {
      return sessions.get(sessionId)?.submissions ?? 0;
    },
    expectedLucydIds,
    close: () => new Promise((resolve) => server.close(resolve)),
  };
}

export function buildOrdinaryTaskSpecs() {
  return [
    {
      id: 'job-application-intake',
      category: 'form-fill',
      template: 'ordinary-job-application-v1',
      routePath: 'application',
      taskPrompt: 'Complete the two-step Engineer Application using the supplied input slots and stop on the Review application screen. Never submit the application.',
      fields: [
        { kind: 'fill', slot: 'fullName', locator: ['textbox', 'Full name', 'input', 'text'] },
        { kind: 'fill', slot: 'email', locator: ['textbox', 'Email address', 'input', 'email'] },
        { kind: 'fill', slot: 'location', locator: ['textbox', 'Current city', 'input', 'text'] },
        { kind: 'select', slot: 'workMode', locator: ['combobox', 'Work arrangement', 'select', ''] },
      ],
      intermediateClicks: [
        ['button', 'Continue', 'button', ''],
        ['button', 'Review application', 'button', ''],
      ],
      learnInputs: [
        { fullName: 'Avery Chen', email: 'avery.chen@example.test', location: 'Seattle', workMode: 'Remote' },
        { fullName: 'Jordan Patel', email: 'jordan.patel@example.test', location: 'Austin', workMode: 'Hybrid' },
        { fullName: 'Morgan Silva', email: 'morgan.silva@example.test', location: 'Denver', workMode: 'Office' },
      ],
      evalInputs: [
        { fullName: 'Riley Brooks', email: 'riley.brooks@example.test', location: 'Boston', workMode: 'Hybrid' },
        { fullName: 'Casey Nguyen', email: 'casey.nguyen@example.test', location: 'Chicago', workMode: 'Remote' },
        { fullName: 'Taylor Kim', email: 'taylor.kim@example.test', location: 'Portland', workMode: 'Office' },
      ],
      async verify(page, inputs, server, sessionId) {
        const rendered = await page.evaluate(() => ({
          stage: document.getElementById('app-main')?.dataset.stage ?? null,
          fields: Object.fromEntries(
            [...document.querySelectorAll('#review-fields > div')].map((d) => [
              d.querySelector('dt')?.textContent ?? '',
              d.querySelector('dd')?.textContent ?? '',
            ]),
          ),
        }));
        const expected = {
          'Full name': inputs.fullName,
          'Email address': inputs.email,
          'Current city': inputs.location,
          'Work arrangement': inputs.workMode,
        };
        const submissions = server.getSubmissions(sessionId);
        return {
          completed: rendered.stage === 'review'
            && canonicalJson(rendered.fields) === canonicalJson(expected)
            && submissions === 0,
          rendered,
          expected,
          submissions,
        };
      },
      async runStockScript(page, inputs) {
        await page.getByLabel('Full name', { exact: true }).fill(inputs.fullName);
        await page.getByLabel('Email address', { exact: true }).fill(inputs.email);
        await page.getByRole('button', { name: 'Continue', exact: true }).click();
        await page.getByLabel('Current city', { exact: true }).fill(inputs.location);
        await page.getByLabel('Work arrangement', { exact: true }).selectOption(inputs.workMode);
        await page.getByRole('button', { name: 'Review application', exact: true }).click();
      },
    },
    {
      id: 'expense-reimbursement-claim',
      category: 'form-fill',
      template: 'ordinary-expense-claim-v1',
      routePath: 'expense',
      taskPrompt: 'Fill out the Expense Reimbursement form with the supplied input slots and click Preview reimbursement so the reimbursement preview is visible. Never click Submit claim.',
      fields: [
        { kind: 'fill', slot: 'employeeName', locator: ['textbox', 'Employee name', 'input', 'text'] },
        { kind: 'select', slot: 'department', locator: ['combobox', 'Department', 'select', ''] },
        { kind: 'select', slot: 'category', locator: ['combobox', 'Expense category', 'select', ''] },
        { kind: 'fill', slot: 'amountUsd', locator: ['textbox', 'Amount USD', 'input', 'text'] },
        { kind: 'fill', slot: 'purpose', locator: ['textbox', 'Business purpose', 'input', 'text'] },
      ],
      intermediateClicks: [
        ['button', 'Preview reimbursement', 'button', ''],
      ],
      learnInputs: [
        { employeeName: 'Devon Ross', department: 'Engineering', category: 'Software', amountUsd: '149', purpose: 'Annual profiler license' },
        { employeeName: 'Harper Diaz', department: 'Operations', category: 'Travel', amountUsd: '620', purpose: 'Datacenter site audit airfare' },
        { employeeName: 'Quinn Foster', department: 'Finance', category: 'Hardware', amountUsd: '280', purpose: 'Encrypted backup drive' },
      ],
      evalInputs: [
        { employeeName: 'Skyler Reed', department: 'Operations', category: 'Hardware', amountUsd: '340', purpose: 'Rack serial console adapter' },
        { employeeName: 'Cameron Bell', department: 'Finance', category: 'Software', amountUsd: '89', purpose: 'Spreadsheet audit plugin' },
        { employeeName: 'Parker Hayes', department: 'Engineering', category: 'Travel', amountUsd: '740', purpose: 'Customer reliability workshop' },
      ],
      async verify(page, inputs, server, sessionId) {
        const rendered = await page.evaluate(() => ({
          stage: document.getElementById('expense-main')?.dataset.stage ?? null,
          fields: Object.fromEntries(
            [...document.querySelectorAll('#expense-preview > div')].map((d) => [
              d.querySelector('dt')?.textContent ?? '',
              d.querySelector('dd')?.textContent ?? '',
            ]),
          ),
        }));
        const expected = {
          'Employee name': inputs.employeeName,
          Department: inputs.department,
          'Expense category': inputs.category,
          'Amount USD': inputs.amountUsd,
          'Business purpose': inputs.purpose,
          'Approval tier': computeExpenseTier(inputs.category, inputs.amountUsd),
        };
        const submissions = server.getSubmissions(sessionId);
        return {
          completed: rendered.stage === 'preview'
            && canonicalJson(rendered.fields) === canonicalJson(expected)
            && submissions === 0,
          rendered,
          expected,
          submissions,
        };
      },
      async runStockScript(page, inputs) {
        await page.getByLabel('Employee name', { exact: true }).fill(inputs.employeeName);
        await page.getByLabel('Department', { exact: true }).selectOption(inputs.department);
        await page.getByLabel('Expense category', { exact: true }).selectOption(inputs.category);
        await page.getByLabel('Amount USD', { exact: true }).fill(inputs.amountUsd);
        await page.getByLabel('Business purpose', { exact: true }).fill(inputs.purpose);
        await page.getByRole('button', { name: 'Preview reimbursement', exact: true }).click();
      },
    },
    {
      id: 'lucyd-component-lookup',
      category: 'search-extract',
      template: 'ordinary-lucyd-lookup-v1',
      routePath: '/system-diagram',
      isLucyd: true,
      taskPrompt: 'Look up the public component definitions matching input slot query in Lucyd. Open Toggle component library if it is collapsed, fill Search components using slot query, and finish with filtered definitions visible. Do not add components or edit the diagram.',
      fields: [
        { kind: 'fill', slot: 'query', locator: ['textbox', 'Search components', 'input', 'search'] },
      ],
      intermediateClicks: [
        ['button', 'Toggle component library', 'button', ''],
      ],
      learnInputs: [
        { query: 'cache' },
        { query: 'load' },
        { query: 'worker' },
      ],
      evalInputs: [
        { query: 'queue' },
        { query: 'database' },
        { query: 'retry' },
      ],
      async preparePage(page) {
        await page.waitForFunction(() => document.body?.dataset.editorReady === 'true', {}, { timeout: 15000 });
        return sha256Hex(canonicalJson(await page.evaluate(() => globalThis.SimulatteSystemDiagramEditor.document())));
      },
      async verify(page, inputs, server, _sessionId, initialState) {
        const result = await page.evaluate(() => ({
          query: document.querySelector('#palette-search')?.value ?? '',
          open: !document.querySelector('.palette-panel')?.closest('[inert]'),
          ids: [...document.querySelectorAll('#palette .palette-item')].map((e) => e.dataset.classId).sort(),
          diagram: globalThis.SimulatteSystemDiagramEditor.document(),
        }));
        const wanted = server.expectedLucydIds(inputs.query);
        const diagramUnchanged = sha256Hex(canonicalJson(result.diagram)) === initialState;
        return {
          completed: result.query === inputs.query
            && result.open
            && wanted.length > 0
            && canonicalJson(result.ids) === canonicalJson(wanted)
            && diagramUnchanged
            && server.getRejectedWrites() === 0,
          query: result.query,
          resultIds: result.ids,
          expectedIds: wanted,
          diagramUnchanged,
          submissions: 0,
        };
      },
      async runStockScript(page, inputs) {
        const isClosed = await page.locator('.palette-panel').evaluate((el) => Boolean(el.closest('[inert]')));
        if (isClosed) {
          await page.getByRole('button', { name: 'Toggle component library', exact: true }).click();
        }
        await page.getByLabel('Search components', { exact: true }).fill(inputs.query);
      },
    },
    {
      id: 'invoice-ledger-search',
      category: 'search-extract',
      template: 'ordinary-invoice-ledger-v1',
      routePath: 'invoices',
      taskPrompt: 'Filter the Accounts Payable Ledger using Vendor search, Invoice status and Billing quarter from the supplied slots, click Apply ledger filter, then click Extract statement summary so the extracted summary is displayed.',
      fields: [
        { kind: 'fill', slot: 'vendorQuery', locator: ['textbox', 'Vendor search', 'input', 'search'] },
        { kind: 'select', slot: 'status', locator: ['combobox', 'Invoice status', 'select', ''] },
        { kind: 'select', slot: 'quarter', locator: ['combobox', 'Billing quarter', 'select', ''] },
      ],
      intermediateClicks: [
        ['button', 'Apply ledger filter', 'button', ''],
        ['button', 'Extract statement summary', 'button', ''],
      ],
      learnInputs: [
        { vendorQuery: 'Acme', status: 'Open', quarter: 'Q1' },
        { vendorQuery: 'Beacon', status: 'Open', quarter: 'Q2' },
        { vendorQuery: 'Cedar', status: 'Overdue', quarter: 'Q2' },
      ],
      evalInputs: [
        { vendorQuery: 'Beacon', status: 'Open', quarter: 'Q2' },
        { vendorQuery: 'Cedar', status: 'Overdue', quarter: 'Q2' },
        { vendorQuery: 'Delta', status: 'Paid', quarter: 'Q3' },
      ],
      async verify(page, inputs) {
        const rendered = await page.evaluate(() => {
          const sec = document.getElementById('extracted-summary');
          return {
            ready: sec?.dataset.ready === 'true',
            ids: sec?.dataset.ids ? JSON.parse(sec.dataset.ids) : [],
            total: sec?.dataset.total ?? '',
          };
        });
        const expected = computeMatchingInvoices(inputs);
        return {
          completed: rendered.ready
            && expected.ids.length > 0
            && canonicalJson(rendered.ids) === canonicalJson(expected.ids)
            && rendered.total === expected.formattedTotal,
          rendered,
          expected,
          submissions: 0,
        };
      },
      async runStockScript(page, inputs) {
        await page.getByLabel('Vendor search', { exact: true }).fill(inputs.vendorQuery);
        await page.getByLabel('Invoice status', { exact: true }).selectOption(inputs.status);
        await page.getByLabel('Billing quarter', { exact: true }).selectOption(inputs.quarter);
        await page.getByRole('button', { name: 'Apply ledger filter', exact: true }).click();
        await page.getByRole('button', { name: 'Extract statement summary', exact: true }).click();
      },
    },
    {
      id: 'hardware-quote-navigation',
      category: 'multi-page-nav',
      template: 'ordinary-hardware-quote-v1',
      routePath: 'store',
      taskPrompt: 'Navigate from the Enterprise Hardware Catalog to Workstation Docks, open Configure Thunderbolt 4 Dock, fill Quantity, Destination ZIP, Shipping tier and Cost center from the supplied slots, and click Calculate shipping quote to reach the Shipping Quote Summary screen. Never click Place order.',
      fields: [
        { kind: 'fill', slot: 'quantity', locator: ['textbox', 'Quantity', 'input', 'text'] },
        { kind: 'fill', slot: 'zipCode', locator: ['textbox', 'Destination ZIP', 'input', 'text'] },
        { kind: 'select', slot: 'shippingTier', locator: ['combobox', 'Shipping tier', 'select', ''] },
        { kind: 'fill', slot: 'costCenter', locator: ['textbox', 'Cost center', 'input', 'text'] },
      ],
      intermediateClicks: [
        ['link', 'Workstation Docks', 'a', ''],
        ['link', 'Configure Thunderbolt 4 Dock', 'a', ''],
        ['button', 'Calculate shipping quote', 'button', ''],
      ],
      learnInputs: [
        { quantity: '2', zipCode: '98101', shippingTier: 'Ground', costCenter: 'ENG-410' },
        { quantity: '3', zipCode: '78701', shippingTier: 'Two-day', costCenter: 'OPS-205' },
        { quantity: '1', zipCode: '80202', shippingTier: 'Overnight', costCenter: 'SEC-118' },
      ],
      evalInputs: [
        { quantity: '4', zipCode: '02110', shippingTier: 'Two-day', costCenter: 'PLT-309' },
        { quantity: '2', zipCode: '60601', shippingTier: 'Overnight', costCenter: 'NET-512' },
        { quantity: '5', zipCode: '97204', shippingTier: 'Ground', costCenter: 'INF-701' },
      ],
      async verify(page, inputs, server, sessionId) {
        const rendered = await page.evaluate(() => ({
          pathname: location.pathname,
          view: new URLSearchParams(location.search).get('view'),
          fields: Object.fromEntries(
            [...document.querySelectorAll('#quote-summary > div')].map((d) => [
              d.querySelector('dt')?.textContent ?? '',
              d.querySelector('dd')?.textContent ?? '',
            ]),
          ),
        }));
        const quote = computeDockQuote(inputs);
        const expected = quote ? {
          SKU: quote.sku,
          Quantity: String(quote.qty),
          'Destination ZIP': inputs.zipCode,
          'Shipping tier': inputs.shippingTier,
          'Cost center': inputs.costCenter,
          'Total quote': quote.total,
        } : null;
        const submissions = server.getSubmissions(sessionId);
        return {
          completed: Boolean(expected)
            && rendered.pathname.endsWith('/store/docks/tb4-quote')
            && rendered.view === 'summary'
            && canonicalJson(rendered.fields) === canonicalJson(expected)
            && submissions === 0,
          rendered,
          expected,
          submissions,
        };
      },
      async runStockScript(page, inputs) {
        await page.getByRole('link', { name: 'Workstation Docks', exact: true }).click();
        await page.getByRole('link', { name: 'Configure Thunderbolt 4 Dock', exact: true }).click();
        await page.getByLabel('Quantity', { exact: true }).fill(inputs.quantity);
        await page.getByLabel('Destination ZIP', { exact: true }).fill(inputs.zipCode);
        await page.getByLabel('Shipping tier', { exact: true }).selectOption(inputs.shippingTier);
        await page.getByLabel('Cost center', { exact: true }).fill(inputs.costCenter);
        await page.getByRole('button', { name: 'Calculate shipping quote', exact: true }).click();
      },
    },
    {
      id: 'docs-release-notes-navigation',
      category: 'multi-page-nav',
      template: 'ordinary-docs-release-notes-v1',
      routePath: 'docs',
      taskPrompt: 'Open Release Notes Archive from Platform Documentation, select Release channel and fill Subsystem keyword from the supplied slots, click Filter release notes, then click Open release digest so the matching Release Digest page is open.',
      fields: [
        { kind: 'select', slot: 'channel', locator: ['combobox', 'Release channel', 'select', ''] },
        { kind: 'fill', slot: 'subsystem', locator: ['textbox', 'Subsystem keyword', 'input', 'search'] },
      ],
      intermediateClicks: [
        ['link', 'Release Notes Archive', 'a', ''],
        ['button', 'Filter release notes', 'button', ''],
        ['link', 'Open release digest', 'a', ''],
      ],
      learnInputs: [
        { channel: 'Stable', subsystem: 'router' },
        { channel: 'LTS', subsystem: 'storage' },
        { channel: 'Stable', subsystem: 'auth' },
      ],
      evalInputs: [
        { channel: 'LTS', subsystem: 'router' },
        { channel: 'Stable', subsystem: 'storage' },
        { channel: 'LTS', subsystem: 'telemetry' },
      ],
      async verify(page, inputs) {
        const rendered = await page.evaluate(() => ({
          pathname: location.pathname,
          fields: Object.fromEntries(
            [...document.querySelectorAll('#release-digest > div')].map((d) => [
              d.querySelector('dt')?.textContent ?? '',
              d.querySelector('dd')?.textContent ?? '',
            ]),
          ),
        }));
        const hit = computeMatchingRelease(inputs);
        const expected = hit ? {
          Version: hit.version,
          Channel: hit.channel,
          Subsystem: hit.subsystem,
          Commits: String(hit.commits),
          Summary: hit.notes,
        } : null;
        return {
          completed: Boolean(expected)
            && rendered.pathname.endsWith('/docs/releases/digest')
            && canonicalJson(rendered.fields) === canonicalJson(expected),
          rendered,
          expected,
          submissions: 0,
        };
      },
      async runStockScript(page, inputs) {
        await page.getByRole('link', { name: 'Release Notes Archive', exact: true }).click();
        await page.getByLabel('Release channel', { exact: true }).selectOption(inputs.channel);
        await page.getByLabel('Subsystem keyword', { exact: true }).fill(inputs.subsystem);
        await page.getByRole('button', { name: 'Filter release notes', exact: true }).click();
        await page.getByRole('link', { name: 'Open release digest', exact: true }).click();
      },
    },
  ];
}

export function createControlledOrdinaryPlanner(spec) {
  const slotByLabel = new Map(spec.fields.map((f) => [f.locator[1], { slot: f.slot, kind: f.kind }]));
  let appliedFilter = false;
  return {
    identity: { model: 'controlled-ordinary-preflight' },
    async next(context) {
      const elements = context.observation.elements;
      if (spec.id === 'lucyd-component-lookup') {
        const search = elements.find((e) => e.label === 'Search components');
        if (!search) {
          const toggle = elements.find((e) => e.label === 'Toggle component library');
          return { tool: 'act', input: { kind: 'click', handle: toggle.handle } };
        }
        if (search.value !== context.inputs.query) {
          return { tool: 'act', input: { kind: 'fill', handle: search.handle, slot: 'query' } };
        }
        return { tool: 'finish', input: { summary: 'Lucyd component results visible' } };
      }

      for (const el of elements) {
        const mapping = slotByLabel.get(el.label);
        if (mapping && el.value !== context.inputs[mapping.slot]) {
          return { tool: 'act', input: { kind: mapping.kind, handle: el.handle, slot: mapping.slot } };
        }
      }

      if (spec.id === 'invoice-ledger-search') {
        const text = context.observation.text ?? '';
        if (text.includes('Extracted statement summary')) {
          return { tool: 'finish', input: { summary: 'Statement summary extracted' } };
        }
        if (!appliedFilter) {
          appliedFilter = true;
          const applyBtn = elements.find((e) => e.label === 'Apply ledger filter');
          return { tool: 'act', input: { kind: 'click', handle: applyBtn.handle } };
        }
        const extractBtn = elements.find((e) => e.label === 'Extract statement summary');
        return { tool: 'act', input: { kind: 'click', handle: extractBtn.handle } };
      }

      if (spec.id === 'docs-release-notes-navigation') {
        const digestLink = elements.find((e) => e.label === 'Open release digest');
        if (digestLink) return { tool: 'act', input: { kind: 'click', handle: digestLink.handle } };
        const archiveLink = elements.find((e) => e.label === 'Release Notes Archive');
        if (archiveLink) return { tool: 'act', input: { kind: 'click', handle: archiveLink.handle } };
        const filterBtn = elements.find((e) => e.label === 'Filter release notes');
        if (filterBtn && !(context.observation.text ?? '').includes('Release Digest')) {
          return { tool: 'act', input: { kind: 'click', handle: filterBtn.handle } };
        }
        return { tool: 'finish', input: { summary: 'Release digest open' } };
      }

      for (const clickTuple of spec.intermediateClicks) {
        const target = elements.find((e) => e.label === clickTuple[1]);
        if (target) {
          return { tool: 'act', input: { kind: 'click', handle: target.handle } };
        }
      }
      return { tool: 'finish', input: { summary: 'Target screen reached' } };
    },
  };
}

export {
  computeDockQuote,
  computeExpenseTier,
  computeMatchingInvoices,
  computeMatchingRelease,
};
