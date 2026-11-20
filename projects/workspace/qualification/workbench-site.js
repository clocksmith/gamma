// Fawn workspace differentiation — frozen multipage workbench fixture with independent oracles.
//
// A three-page catalog whose prices and stock update in place, an optional activity panel that
// changes continuously, a cart, a checkout form, orders and invoices. A human is simulated inside
// the page (no automation channel) from queued actions. The server's own mutation log, cart and
// orders decide success and incorrect actions; agents and services never report them.

import { createHash } from 'node:crypto';
import { createServer } from 'node:http';

const LOOPBACK = '127.0.0.1';
const SEE_OTHER = 303;
const NOT_FOUND = 404;
const POLL_MS = 100;
const ACTIVITY_ROWS = 40;
const TRANSIENT_CONFIRMATION_MS = 1000;
const PAGE_COUNT = 3;

const CATALOG = Object.freeze([
  { page: 1, slug: 'widget-a', name: 'Widget A', price: 1450, stock: 5 },
  { page: 1, slug: 'widget-b', name: 'Widget B', price: 700, stock: 0 },
  { page: 1, slug: 'widget-c', name: 'Widget C', price: 2100, stock: 2 },
  { page: 1, slug: 'widget-d', name: 'Widget D', price: 1180, stock: 9 },
  { page: 2, slug: 'gadget-a', name: 'Gadget A', price: 1320, stock: 3 },
  { page: 2, slug: 'gadget-b', name: 'Gadget B', price: 900, stock: 4 },
  { page: 2, slug: 'gadget-c', name: 'Gadget C', price: 3000, stock: 1 },
  { page: 2, slug: 'gadget-d', name: 'Gadget D', price: 1990, stock: 6 },
  { page: 3, slug: 'gizmo-a', name: 'Gizmo A', price: 950, stock: 2 },
  { page: 3, slug: 'gizmo-b', name: 'Gizmo B', price: 650, stock: 0 },
  { page: 3, slug: 'gizmo-c', name: 'Gizmo C', price: 1100, stock: 8 },
  { page: 3, slug: 'gizmo-d', name: 'Gizmo D', price: 2500, stock: 1 },
]);

const money = (cents) => `$${(cents / 100).toFixed(2)}`;
const stockText = (stock) => (stock > 0 ? `${stock} in stock` : 'out of stock');

function escapeHtml(text) {
  return String(text).replace(/[&<>"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[char]);
}

function page(title, body) {
  return `<!doctype html><html><head><title>${title}</title></head><body>${body}</body></html>`;
}

function catalogPage(state, number) {
  const rows = state.items.filter((item) => item.page === number).map((item) => `
    <li class="product-row" id="row-${item.slug}"><span class="name">${item.name}</span>
      <span class="price">${money(item.price)}</span> <span class="stock">${stockText(item.stock)}</span>
      <button class="add" data-item="${item.slug}">Add to cart</button></li>`).join('');
  const activity = state.setup.churn
    ? `<section id="activity"><h2>Market activity</h2><ol>${Array.from({ length: ACTIVITY_ROWS }, (_, index) => `<li id="act-${index}">Trade ${index}: waiting</li>`).join('')}</ol></section>`
    : '';
  return page(`Catalog page ${number}`, `
  <h1>Catalog</h1>
  <p id="clock">tick 0</p>
  <nav id="pager">Page ${number} of ${PAGE_COUNT}</nav>
  <p id="cart-summary">${cartSummary(state)}</p>
  <ul id="products">${rows}</ul>
  ${activity}
  <script>
    (() => {
      let tick = 0;
      const format = (cents) => '$' + (cents / 100).toFixed(2);
      document.querySelectorAll('button.add').forEach((button) => button.addEventListener('click', async () => {
        const response = await fetch('/cart/add', { method: 'POST', body: button.dataset.item });
        document.getElementById('cart-summary').textContent = await response.text();
      }));
      setInterval(async () => {
        tick += 1;
        document.getElementById('clock').textContent = 'tick ' + tick;
        const state = await (await fetch('/catalog/state?page=${number}')).json();
        for (const item of state.items) {
          const row = document.getElementById('row-' + item.slug);
          const price = format(item.price);
          const stock = item.stock > 0 ? item.stock + ' in stock' : 'out of stock';
          if (row.querySelector('.price').textContent !== price) row.querySelector('.price').textContent = price;
          if (row.querySelector('.stock').textContent !== stock) row.querySelector('.stock').textContent = stock;
        }
        if (state.churn) {
          document.querySelectorAll('#activity li').forEach((row, index) => {
            row.textContent = 'Trade ' + index + ': ' + ((index * 7919 + tick * 104729) % 9973) + ' units at tick ' + tick;
          });
        }
      }, ${POLL_MS});
    })();
  </script>`);
}

function cartSummary(state) {
  if (state.cart.length === 0) return 'Cart: empty';
  return `Cart: ${state.cart.map((line) => `${line.name} (${money(line.price)})`).join(', ')}`;
}

function cartPage(state) {
  const rows = state.cart.map((line) => `<li class="cart-row" id="cart-${line.slug}"><span class="name">${line.name}</span>
    <span class="price">${money(line.price)}</span> <button class="remove" data-item="${line.slug}">Remove</button></li>`).join('');
  const total = state.cart.reduce((sum, line) => sum + line.price, 0);
  return page('Cart', `
  <h1>Cart</h1>
  <ul id="cart-items">${rows}</ul>
  <p id="cart-total">Total: ${money(total)}</p>
  <a id="checkout" href="/checkout">Checkout</a>
  <script>
    document.querySelectorAll('button.remove').forEach((button) => button.addEventListener('click', async () => {
      await fetch('/cart/remove', { method: 'POST', body: button.dataset.item });
      button.closest('li').remove();
      document.getElementById('cart-total').textContent = 'Total: ' + await (await fetch('/cart/total')).text();
    }));
  </script>`);
}

function checkoutPage(state) {
  const reference = state.setup.idempotency ? '<label>Reference <input id="reference" name="reference"></label>' : '';
  return page('Checkout', `
  <h1>Checkout</h1>
  <form id="order-form" method="post" action="/orders">
    <label>Address <input id="address" name="address"></label>
    ${reference}
    <button id="place" type="submit">Place order</button>
  </form>
  <script>
    // A person at the same browser: actions arrive from the human queue, not an automation channel.
    setInterval(async () => {
      const next = await (await fetch('/human/next')).json();
      if (!next) return;
      const field = document.getElementById('address');
      field.value = next.fill;
      field.dispatchEvent(new Event('input', { bubbles: true }));
      await fetch('/human/done', { method: 'POST', body: next.fill });
    }, ${POLL_MS});
  </script>`);
}

function confirmationPage(state, order) {
  const redirect = state.setup.transientConfirmation && !order.viewed
    ? `<script>setTimeout(() => { location.href = '/catalog?page=1'; }, ${TRANSIENT_CONFIRMATION_MS});</script>`
    : '';
  order.viewed = true;
  return page('Order placed', `
  <h1>Order ${order.id} placed</h1>
  <p id="order-detail">Ship to: ${escapeHtml(order.address)}; reference: ${escapeHtml(order.reference || 'none')}</p>
  <a id="invoice" href="/orders/${order.id}/invoice.csv">Download invoice</a>
  ${redirect}`);
}

function invoiceBytes(order) {
  return Buffer.from(`order,${order.id}\n${order.lines.map((line) => `item,${line.slug},${line.price}`).join('\n')}\naddress,${order.address}\n`);
}

function sha256Hex(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

async function readBody(request) {
  let raw = '';
  for await (const chunk of request) raw += chunk;
  return raw;
}

/**
 * Start the workbench. `setup` flags: churn, orderList, idempotency, transientConfirmation.
 * `hold({method, path})` holds the next matching response after its effect is recorded.
 */
async function startWorkbenchSite() {
  const state = {
    setup: { churn: false, orderList: true, idempotency: true, transientConfirmation: false },
    items: CATALOG.map((item) => ({ ...item })),
    cart: [],
    orders: [],
    mutations: [],
    humanQueue: [],
    requests: [],
  };
  const holds = [];
  const mutate = (kind, details) => {
    const entry = { seq: state.mutations.length + 1, at: new Date().toISOString(), kind, ...details };
    state.mutations.push(entry);
    return entry;
  };
  const itemOf = (slug) => state.items.find((item) => item.slug === slug);
  const holdIfRequested = async (method, path, entry) => {
    const index = holds.findIndex((held) => held.method === method && held.path === path);
    if (index === -1) return;
    const [held] = holds.splice(index, 1);
    held.reach(entry);
    await held.released;
  };
  const respond = (response, status, body, headers = {}) => {
    try {
      response.writeHead(status, { 'content-type': 'text/html; charset=utf-8', ...headers });
      response.end(body);
    } catch {
      // The browser that asked is gone; the application state already changed.
    }
  };
  const json = (response, value) => respond(response, 200, JSON.stringify(value), { 'content-type': 'application/json' });

  const ROUTES = [
    ['GET', /^\/catalog$/, (request, response, url) => {
      const number = Number(url.searchParams.get('page') ?? 1);
      if (!(number >= 1 && number <= PAGE_COUNT)) return respond(response, NOT_FOUND, page('Not found', ''));
      return respond(response, 200, catalogPage(state, number));
    }],
    ['GET', /^\/catalog\/state$/, (request, response, url) => {
      const number = Number(url.searchParams.get('page'));
      return json(response, { churn: state.setup.churn, items: state.items.filter((item) => item.page === number) });
    }],
    ['POST', /^\/cart\/add$/, async (request, response) => {
      const item = itemOf(await readBody(request));
      if (!item) return respond(response, NOT_FOUND, 'unknown item');
      mutate('cart-add', { item: item.slug, price: item.price, stock: item.stock });
      state.cart.push({ slug: item.slug, name: item.name, price: item.price });
      return respond(response, 200, cartSummary(state), { 'content-type': 'text/plain' });
    }],
    ['POST', /^\/cart\/remove$/, async (request, response) => {
      const slug = await readBody(request);
      const index = state.cart.findIndex((line) => line.slug === slug);
      if (index !== -1) state.cart.splice(index, 1);
      mutate('cart-remove', { item: slug });
      return respond(response, 200, 'removed', { 'content-type': 'text/plain' });
    }],
    ['GET', /^\/cart\/total$/, (request, response) => respond(response, 200, money(state.cart.reduce((sum, line) => sum + line.price, 0)),
      { 'content-type': 'text/plain' })],
    ['GET', /^\/cart$/, (request, response) => respond(response, 200, cartPage(state))],
    ['GET', /^\/checkout$/, (request, response) => respond(response, 200, checkoutPage(state))],
    ['GET', /^\/human\/next$/, (request, response) => json(response, state.humanQueue.shift() ?? null)],
    ['POST', /^\/human\/done$/, async (request, response) => {
      mutate('human-fill', { value: await readBody(request) });
      return json(response, true);
    }],
    ['POST', /^\/orders$/, async (request, response) => {
      const fields = Object.fromEntries(new URLSearchParams(await readBody(request)));
      const reference = state.setup.idempotency ? (fields.reference ?? '') : '';
      const duplicateOf = reference ? state.orders.find((order) => order.reference === reference) : null;
      let order = duplicateOf;
      if (!order) {
        order = {
          id: state.orders.length + 1,
          lines: state.cart.map((line) => ({ ...line, priceAtOrder: itemOf(line.slug).price, stockAtOrder: itemOf(line.slug).stock })),
          address: fields.address ?? '',
          reference,
          catalogAtOrder: state.items.map((item) => ({ ...item })),
          viewed: false,
        };
        state.orders.push(order);
        state.cart = [];
      }
      const entry = mutate('order', { orderId: order.id, duplicateOf: duplicateOf?.id ?? null, address: order.address });
      await holdIfRequested('POST', '/orders', entry);
      return respond(response, SEE_OTHER, '', { location: `/orders/${order.id}` });
    }],
    ['GET', /^\/orders$/, (request, response) => {
      if (!state.setup.orderList) return respond(response, NOT_FOUND, page('Not found', ''));
      const rows = state.orders.map((order) => `<li id="order-${order.id}">Order ${order.id}: ${order.lines.map((line) => line.name).join(', ')}`
        + ` to ${escapeHtml(order.address)}; reference ${escapeHtml(order.reference || 'none')}</li>`).join('');
      return respond(response, 200, page('Orders', `<h1>Orders</h1><ul id="orders">${rows}</ul>`));
    }],
    ['GET', /^\/orders\/(\d+)$/, (request, response, url, match) => {
      const order = state.orders.find((candidate) => candidate.id === Number(match[1]));
      return order ? respond(response, 200, confirmationPage(state, order)) : respond(response, NOT_FOUND, page('Not found', ''));
    }],
    ['GET', /^\/orders\/(\d+)\/invoice\.csv$/, (request, response, url, match) => {
      const order = state.orders.find((candidate) => candidate.id === Number(match[1]));
      if (!order) return respond(response, NOT_FOUND, '');
      const bytes = invoiceBytes(order);
      mutate('invoice', { orderId: order.id, sha256: sha256Hex(bytes) });
      return respond(response, 200, bytes, {
        'content-type': 'text/csv',
        'content-disposition': `attachment; filename="invoice-${order.id}.csv"`,
      });
    }],
    ['GET', /^\/control\/setup$/, (request, response, url) => {
      for (const flag of Object.keys(state.setup)) {
        if (url.searchParams.has(flag)) state.setup[flag] = url.searchParams.get(flag) === '1';
      }
      return json(response, state.setup);
    }],
    ['GET', /^\/control\/price$/, (request, response, url) => {
      const item = itemOf(url.searchParams.get('item'));
      item.price = Number(url.searchParams.get('price'));
      mutate('price-change', { item: item.slug, price: item.price });
      return json(response, item);
    }],
    ['GET', /^\/control\/human$/, (request, response, url) => {
      state.humanQueue.push({ fill: url.searchParams.get('fill') });
      return json(response, true);
    }],
  ];

  const server = createServer(async (request, response) => {
    const url = new URL(request.url, `http://${request.headers.host}`);
    state.requests.push({ at: new Date().toISOString(), method: request.method, path: url.pathname, search: url.search });
    for (const [method, pattern, handler] of ROUTES) {
      const match = pattern.exec(url.pathname);
      if (match && request.method === method) return handler(request, response, url, match);
    }
    return respond(response, NOT_FOUND, page('Not found', '<p>Not found</p>'));
  });
  const origin = await new Promise((resolve) => {
    server.listen(0, LOOPBACK, () => resolve(`http://${LOOPBACK}:${server.address().port}`));
  });
  return {
    origin,
    pageCount: PAGE_COUNT,
    state,
    invoiceSha256: (order) => sha256Hex(invoiceBytes(order)),
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
    close: () => new Promise((done) => {
      server.closeAllConnections();
      server.close(done);
    }),
  };
}

export { CATALOG, startWorkbenchSite };
