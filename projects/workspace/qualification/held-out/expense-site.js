// Fawn workspace differentiation — held-out expense filing application.
//
// Implemented after the model-driven suite was frozen, to its specification in
// model-agent/held-out-workflows.json, and never used to tune prompts or tools. A receipts
// inbox keeps receiving new receipts at the top; each receipt can be filed once as an expense.
// The server's own expenses and mutation log decide success and incorrect actions.

import { createHash } from 'node:crypto';
import { createServer } from 'node:http';

const LOOPBACK = '127.0.0.1';
const SEE_OTHER = 303;
const NOT_FOUND = 404;
const POLL_MS = 100;
const ARRIVAL_MS = 3000;
const BUSY_ARRIVAL_MS = 150;
const TRANSIENT_CONFIRMATION_MS = 1000;
const CATEGORIES = Object.freeze(['Meals', 'Travel', 'Lodging', 'Supplies']);

const RECEIPTS = Object.freeze([
  { id: 'R101', merchant: 'Corner Bakery', date: '2026-10-11', cents: 1240 },
  { id: 'R102', merchant: 'Harbor Rail', date: '2026-10-09', cents: 8640 },
  { id: 'R103', merchant: 'Office Depot', date: '2026-10-08', cents: 3299 },
  { id: 'R104', merchant: 'Harbor Rail', date: '2026-10-02', cents: 4320 },
  { id: 'R105', merchant: 'Lakeside Inn', date: '2026-10-01', cents: 21900 },
]);

const ARRIVAL_MERCHANTS = Object.freeze(['Metro Taxi', 'Cafe Lumen', 'Print Hub', 'Airport Parking', 'Book Barn', 'Noodle Bar']);
const money = (cents) => `$${(cents / 100).toFixed(2)}`;

function page(title, body) {
  return `<!doctype html><html><head><title>${title}</title></head><body>${body}</body></html>`;
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[char]);
}

const receiptRow = (receipt) => `<li class="receipt-row" id="receipt-${receipt.id}"><span class="merchant">${escapeHtml(receipt.merchant)}</span>
  <span class="date">${receipt.date}</span> <span class="amount">${money(receipt.cents)}</span>
  <a class="open" href="/receipts/${receipt.id}">Open</a></li>`;

function inboxPage(state) {
  return page('Receipts', `
  <h1>Receipts inbox</h1>
  <ul id="receipts">${state.receipts.map(receiptRow).join('')}</ul>
  <script>
    (() => {
      let seen = ${state.receipts.length};
      setInterval(async () => {
        const state = await (await fetch('/receipts/state?since=' + seen)).json();
        for (const html of state.arrivals) document.getElementById('receipts').insertAdjacentHTML('afterbegin', html);
        seen = state.total;
      }, ${POLL_MS});
    })();
  </script>`);
}

function receiptPage(receipt) {
  const options = CATEGORIES.map((category) => `<option value="${category}">${category}</option>`).join('');
  return page(`Receipt ${receipt.id}`, `
  <h1>Receipt from ${escapeHtml(receipt.merchant)}</h1>
  <p id="receipt-detail">Date ${receipt.date}; amount ${money(receipt.cents)}</p>
  <form id="expense-form" method="post" action="/receipts/${receipt.id}/file">
    <label>Category <select id="category" name="category"><option value="">Choose</option>${options}</select></label>
    <label>Amount <input id="amount" name="amount"></label>
    <button id="file" type="submit">File expense</button>
  </form>`);
}

function reportPage(state, expense) {
  const redirect = state.setup.transientConfirmation && !expense.viewed
    ? `<script>setTimeout(() => { location.href = '/receipts'; }, ${TRANSIENT_CONFIRMATION_MS});</script>`
    : '';
  expense.viewed = true;
  return page('Expense filed', `
  <h1>Expense ${expense.id} filed</h1>
  <p id="expense-detail">${escapeHtml(expense.receipt.merchant)}, ${expense.receipt.date}, ${escapeHtml(expense.category)}, ${escapeHtml(expense.amount)}</p>
  <a id="download" href="/reports/${expense.id}/report.csv">Download report</a>
  ${redirect}`);
}

function reportBytes(expense) {
  return Buffer.from(`expense,${expense.id}\nreceipt,${expense.receipt.id}\nmerchant,${expense.receipt.merchant}\n`
    + `category,${expense.category}\namount,${expense.amount}\n`);
}

const sha256Hex = (bytes) => createHash('sha256').update(bytes).digest('hex');

async function readBody(request) {
  let raw = '';
  for await (const chunk of request) raw += chunk;
  return raw;
}

/** Start the expense system. `setup` flags: churn (busy inbox), transientConfirmation. No report list. */
async function startExpenseSite() {
  const state = {
    setup: { churn: false, transientConfirmation: false },
    receipts: RECEIPTS.map((receipt) => ({ ...receipt })),
    expenses: [],
    mutations: [],
    requests: [],
  };
  const holds = [];
  const mutate = (kind, details) => {
    const entry = { seq: state.mutations.length + 1, at: new Date().toISOString(), kind, ...details };
    state.mutations.push(entry);
    return entry;
  };
  let arrivals = 0;
  let lastArrival = Date.now();
  const arrive = setInterval(() => {
    const interval = state.setup.churn ? BUSY_ARRIVAL_MS : ARRIVAL_MS;
    if (Date.now() - lastArrival < interval) return;
    lastArrival = Date.now();
    arrivals += 1;
    state.receipts.unshift({
      id: `R${200 + arrivals}`,
      merchant: ARRIVAL_MERCHANTS[arrivals % ARRIVAL_MERCHANTS.length],
      date: '2026-10-14',
      cents: 500 + ((arrivals * 733) % 9000),
    });
  }, BUSY_ARRIVAL_MS / 3);
  arrive.unref();
  const respond = (response, status, body, headers = {}) => {
    try {
      response.writeHead(status, { 'content-type': 'text/html; charset=utf-8', ...headers });
      response.end(body);
    } catch {
      // The browser that asked is gone; the filing already changed.
    }
  };
  const missing = (response) => respond(response, NOT_FOUND, page('Not found', '<h1>Not found</h1>'));
  const receiptOf = (id) => state.receipts.find((receipt) => receipt.id === id);
  const ROUTES = [
    ['GET', /^\/$/, (request, response) => respond(response, 200, page('Expenses', '<h1>Expenses</h1><nav><a href="/receipts">Receipts inbox</a></nav>'))],
    ['GET', /^\/receipts$/, (request, response) => respond(response, 200, inboxPage(state))],
    ['GET', /^\/receipts\/state$/, (request, response, url) => {
      const since = Number(url.searchParams.get('since') ?? state.receipts.length);
      const added = state.receipts.slice(0, Math.max(0, state.receipts.length - since)).reverse();
      return respond(response, 200, JSON.stringify({ total: state.receipts.length, arrivals: added.map(receiptRow) }),
        { 'content-type': 'application/json' });
    }],
    ['GET', /^\/receipts\/(R\d+)$/, (request, response, url, match) => {
      const receipt = receiptOf(match[1]);
      return receipt ? respond(response, 200, receiptPage(receipt)) : missing(response);
    }],
    ['POST', /^\/receipts\/(R\d+)\/file$/, async (request, response, url, match) => {
      const receipt = receiptOf(match[1]);
      if (!receipt) return missing(response);
      const fields = Object.fromEntries(new URLSearchParams(await readBody(request)));
      const expense = { id: state.expenses.length + 1, receipt: { ...receipt }, category: fields.category ?? '',
        amount: fields.amount ?? '', viewed: false };
      state.expenses.push(expense);
      const entry = mutate('expense', { expenseId: expense.id, receipt: receipt.id, category: expense.category, amount: expense.amount });
      const index = holds.findIndex((held) => held.method === 'POST' && new RegExp(held.pathPattern).test(url.pathname));
      if (index !== -1) {
        const [held] = holds.splice(index, 1);
        held.reach(entry);
        await held.released;
      }
      return respond(response, SEE_OTHER, '', { location: `/reports/${expense.id}` });
    }],
    ['GET', /^\/reports\/(\d+)$/, (request, response, url, match) => {
      const expense = state.expenses.find((candidate) => candidate.id === Number(match[1]));
      return expense ? respond(response, 200, reportPage(state, expense)) : missing(response);
    }],
    ['GET', /^\/reports\/(\d+)\/report\.csv$/, (request, response, url, match) => {
      const expense = state.expenses.find((candidate) => candidate.id === Number(match[1]));
      if (!expense) return missing(response);
      const bytes = reportBytes(expense);
      mutate('download', { expenseId: expense.id, sha256: sha256Hex(bytes) });
      return respond(response, 200, bytes, { 'content-type': 'text/csv', 'content-disposition': `attachment; filename="expense-${expense.id}.csv"` });
    }],
    ['GET', /^\/control\/setup$/, (request, response, url) => {
      for (const flag of Object.keys(state.setup)) {
        if (url.searchParams.has(flag)) state.setup[flag] = url.searchParams.get(flag) === '1';
      }
      return respond(response, 200, JSON.stringify(state.setup), { 'content-type': 'application/json' });
    }],
  ];
  const server = createServer(async (request, response) => {
    const url = new URL(request.url, `http://${request.headers.host}`);
    state.requests.push({ at: new Date().toISOString(), method: request.method, path: url.pathname });
    for (const [method, pattern, handler] of ROUTES) {
      const match = pattern.exec(url.pathname);
      if (match && request.method === method) return handler(request, response, url, match);
    }
    return missing(response);
  });
  const origin = await new Promise((resolve) => {
    server.listen(0, LOOPBACK, () => resolve(`http://${LOOPBACK}:${server.address().port}`));
  });
  return {
    origin,
    state,
    money,
    reportSha256: (expense) => sha256Hex(reportBytes(expense)),
    hold({ method, pathPattern }) {
      let reach;
      let release;
      const reached = new Promise((resolve) => {
        reach = resolve;
      });
      const released = new Promise((resolve) => {
        release = resolve;
      });
      holds.push({ method, pathPattern, reach, released });
      return { reached, release };
    },
    close: () => new Promise((done) => {
      clearInterval(arrive);
      server.closeAllConnections();
      server.close(done);
    }),
  };
}

export { startExpenseSite };
