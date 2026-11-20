// Controlled merchant. Browser inputs create its order; the independent oracle
// checks server truth and submission counts, never the agent's completion claim.
import { createServer } from 'node:http';
import { randomUUID } from 'node:crypto';
import { catalogFor, requestFor } from './cases.js';

const escape = text => String(text).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('"', '&quot;');
export async function shoppingFixture() {
  const sessions = new Map();
  const server = createServer(async (req, res) => {
    const url = new URL(req.url, 'http://fixture'), [, id, route = 'search', sku] = url.pathname.split('/');
    const session = sessions.get(id);
    if (!session) { res.writeHead(404); res.end(); return; }
    const request = session.request;
    let state = { phase: route, accountId: session.accountId }, content = '';
    const button = (text, path) => `<button type="button" onclick="location.href=${escape(JSON.stringify(path))}">${escape(text)}</button>`;
    const facts = value => Object.entries(value).map(([key, item]) => `<div><dt>${escape(key)}</dt><dd>${escape(typeof item === 'object' ? JSON.stringify(item) : item)}</dd></div>`).join('');
    const input = (slot, label, type = 'text') => `<label>${label}<input name="${slot}" type="${type}" required></label>`;
    if (route === 'search') content = `<form action="/${id}/results">${input('query', 'Search products')}<button type="submit">Search</button></form>`;
    else if (route === 'results') {
      state.offers = session.catalog;
      content = session.catalog.map(offer => `<article><h2>${escape(offer.sku)}</h2><dl>${facts(offer)}</dl>${button(`View ${offer.sku}`, `/${id}/detail/${offer.sku}`)}</article>`).join('');
    } else if (route === 'detail') {
      const offer = session.catalog.find(item => item.sku === sku);
      if (!offer) { res.writeHead(404); res.end(); return; }
      state.offers = [offer]; session.selected = offer;
      content = `<h2>${escape(offer.sku)}</h2><dl>${facts(offer)}</dl>${button('Add to cart', `/${id}/shipping`)}`;
    } else if (route === 'shipping') {
      if (session.fault === 'account-change') session.accountId = state.accountId = 'different-shopper';
      const fields = [input('recipient', 'Recipient'), input('address', 'Street address'),
        input('postalCode', session.fault === 'layout-change' ? 'ZIP code' : 'Postal code')];
      if (session.fault === 'layout-change') fields.reverse();
      content = `<form action="/${id}/review">${fields.join('')}<label>Shipping<select name="shipping"><option>Choose</option><option>Standard</option><option>Express</option></select></label><button type="submit">Review order</button></form>`;
    } else if (route === 'review') {
      const selected = structuredClone(session.selected);
      if (session.fault === 'price-change') selected.unitCents = request.maxTotalCents + 10000;
      if (session.fault === 'out-of-stock') selected.stock = 0;
      session.current = selected;
      session.quote = { sku: selected.sku, category: selected.category, specs: selected.specs,
        unitCents: selected.unitCents, shippingCents: selected.shippingCents, taxCents: selected.taxCents,
        totalCents: selected.unitCents * request.quantity + selected.shippingCents + selected.taxCents,
        quantity: request.quantity, accountId: session.accountId, recipient: url.searchParams.get('recipient'),
        address: url.searchParams.get('address'), postalCode: url.searchParams.get('postalCode'), shipping: url.searchParams.get('shipping') };
      state.quote = session.quote;
      state.offers = [selected];
      content = `<dl>${facts(session.quote)}</dl><p>Stock: ${selected.stock}</p><form method="post" action="/${id}/purchase"><button type="submit">Place order</button></form>`;
    } else if (route === 'purchase' && req.method === 'POST') {
      for await (const _ of req) { /* drain form body */ }
      session.submissions++;
      if (session.current?.stock >= request.quantity && session.quote) {
        session.orders.push({ operationId: id, orderId: randomUUID(), quote: structuredClone(session.quote) });
      }
      res.writeHead(303, { location: `/${id}/receipt` }); res.end(); return;
    } else if (route === 'receipt') {
      state.receipt = session.fault === 'missing-receipt' ? null : session.orders.at(-1) ?? null;
      content = state.receipt ? `<p id="receipt">Order confirmed ${escape(id)}</p><dl>${facts(state.receipt.quote)}</dl>` : '<p>Receipt unavailable. Check order history.</p>';
    } else { res.writeHead(404); res.end(); return; }
    // The site adapter reads this visible machine-readable accessibility block.
    // It contains the same current facts as the rendered page, never oracle labels.
    const data = `<details><summary>Structured storefront facts</summary><pre>${escape(JSON.stringify(state))}</pre></details>`;
    res.setHeader('content-type', 'text/html');
    res.end(`<!doctype html><title>Fawn controlled shop</title><style>body{font:16px system-ui;max-width:980px;margin:40px auto;padding:20px}article{display:inline-block;vertical-align:top;padding:16px;border:1px solid #bbb;margin:8px}label{display:block;margin:18px 0}input,select,button{padding:10px}dt,dd{display:inline;margin:0 8px 0 0}details{margin-top:32px}</style><h1>Controlled shop</h1><p id="phase">${escape(route)}</p><p>Account: ${escape(state.accountId)}</p>${content}${data}<script>document.querySelector('details').open=true</script>`);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  return { origin,
    add(id, index, fault = null) {
      sessions.set(id, { request: requestFor(index), catalog: catalogFor(index), fault, accountId: 'test-shopper', orders: [], submissions: 0 });
      return `${origin}/${id}/search`;
    },
    oracle(id) {
      const session = sessions.get(id), r = session.request;
      // Independent selection: no import of the production eligibility/ranking/quote functions.
      const candidates = session.catalog.filter(p => p.category === r.category && p.stock >= r.quantity
        && Object.keys(r.minimums).every(key => p.specs[key] >= r.minimums[key])
        && p.unitCents * r.quantity + p.shippingCents + p.taxCents <= r.maxTotalCents)
        .sort((a, b) => (a.unitCents * r.quantity + a.shippingCents + a.taxCents) - (b.unitCents * r.quantity + b.shippingCents + b.taxCents) || a.sku.localeCompare(b.sku));
      const expected = candidates[0];
      const wrongOrders = session.orders.filter(({ quote: q }) => !expected || q.sku !== expected.sku
        || q.unitCents !== expected.unitCents || q.totalCents !== expected.unitCents * r.quantity + expected.shippingCents + expected.taxCents
        || q.totalCents > r.maxTotalCents || q.quantity !== r.quantity || session.current.stock < r.quantity
        || ['accountId', 'recipient', 'address', 'postalCode', 'shipping'].some(key => q[key] !== r[key])).length;
      return { submissions: session.submissions, orderCount: session.orders.length, wrongOrders,
        duplicateOrders: Math.max(0, session.orders.length - 1), selectedSku: session.orders[0]?.quote.sku ?? null,
        completed: session.orders.length === 1 && wrongOrders === 0 && session.submissions === 1 };
    },
    close: () => new Promise(resolve => server.close(resolve)),
  };
}

export function fixtureSite(origin) {
  return { id: 'controlled-storefront-v1', origin,
    transitions: Object.fromEntries([['Search', 'results'], ['Review order', 'review']].map(([label, phase]) => [label, {
      kind: 'submit', authorizedIntent: 'shopping-browse', completion: { completedWhen: [
        { kind: 'element-text-includes', selector: '#phase', value: phase },
      ] },
    }])),
    read(observation) {
      const marker = 'Structured storefront facts\n', start = observation.text.lastIndexOf(marker);
      if (start < 0) throw Error('Storefront facts missing');
      return JSON.parse(observation.text.slice(start + marker.length).trim());
    },
    fields: { search: [{ kind: 'fill', slot: 'query', labels: ['Search products'] }], shipping: [
      { kind: 'fill', slot: 'recipient', labels: ['Recipient'] },
      { kind: 'fill', slot: 'address', labels: ['Street address'] },
      { kind: 'fill', slot: 'postalCode', labels: ['Postal code', 'ZIP code'] },
      { kind: 'select', slot: 'shipping', labels: ['Shipping'] },
    ] },
    receiptConditions: operationId => [{ kind: 'element-text-includes', selector: '#receipt', value: `Order confirmed ${operationId}` }],
  };
}
