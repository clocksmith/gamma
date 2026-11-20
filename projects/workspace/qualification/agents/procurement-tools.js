// Fawn workspace differentiation — the procurement workbench as each arm sees it.

import { completedUrl } from './fawn-agent.js';
import { cents, controls } from './outline.js';

const FAWN_VIEWS = Object.freeze({
  catalog: { regionGroups: ['.product-row'], regions: ['#pager', '#cart-summary'] },
  cart: { regionGroups: ['.cart-row'], regions: ['#cart-total'] },
  checkout: { regions: ['#order-form', '#address', '#reference'] },
  confirmation: { regions: ['h1', '#invoice'] },
});

const FAWN_PARSERS = Object.freeze({
  catalog: (regions, version) => ({
    items: Object.entries(regions).filter(([selector]) => selector.startsWith('#row-')).map(([selector, outline]) => {
      const [name, price, stock] = outline.split(' | ');
      return {
        name,
        price: cents(price),
        stock: stock === 'out of stock' ? 0 : Number.parseInt(stock, 10),
        handle: controls(outline).find((control) => control.name === 'Add to cart')?.handle,
        region: selector,
        version,
      };
    }),
  }),
  cart: (regions, version) => ({
    lines: Object.entries(regions).filter(([selector]) => selector.startsWith('#cart-') && selector !== '#cart-total')
      .map(([selector, outline]) => ({
        name: outline.split(' | ')[0],
        price: cents(outline),
        handle: controls(outline).find((control) => control.name === 'Remove')?.handle,
        region: selector,
        version,
      })),
  }),
  checkout: (regions, version) => {
    const fields = controls(regions['#order-form'] ?? '');
    // Each field decision depends on that field alone, so the agent's own fill of one field
    // does not stale its decision about the next.
    const field = (name) => {
      const control = fields.find((candidate) => candidate.name === name);
      return control ? { handle: control.handle, value: control.value ?? '', version, region: `#${name}` } : null;
    };
    return {
      address: field('address'),
      reference: field('reference'),
      place: { handle: fields.find((control) => control.name === 'Place order')?.handle, version },
    };
  },
  confirmation: (regions, version) => {
    const link = controls(regions['#invoice'] ?? '').find((control) => control.name === 'Download invoice');
    return { orderId: Number(/Order (\d+) placed/.exec(regions.h1 ?? '')?.[1]) || null, invoice: link ? { handle: link.handle, version } : null };
  },
});

const orderIdOf = (record) => Number(/\/orders\/(\d+)/.exec(completedUrl(record))?.[1]) || null;

const FAWN_ACTIONS = Object.freeze({
  add: (target, options, { base, actionId, scoped, task, sequence }) => ({
    ...base,
    actionId: actionId('add'),
    kind: 'click',
    ...scoped([target.region]),
    effect: { external: true, effectKey: `cart-add:${task.id}:${target.name}:${sequence()}` },
    completion: { completedWhen: [{ kind: 'element-text-includes', selector: '#cart-summary', value: target.name }] },
  }),
  remove: (target, options, { base, actionId, scoped, task, sequence }) => ({
    ...base,
    actionId: actionId('remove'),
    kind: 'click',
    ...scoped([target.region]),
    effect: { external: true, effectKey: `cart-remove:${task.id}:${target.name}:${sequence()}` },
    completion: { completedWhen: [{ kind: 'element-absent', selector: target.region }] },
  }),
  fill: (target, { value }, { base, actionId, scoped }) => ({ ...base, actionId: actionId('fill'), kind: 'fill', ...scoped([target.region]), params: { value } }),
  place: (target, { reference }, { base, actionId, scoped, task }) => ({
    ...base,
    actionId: actionId('place'),
    kind: 'submit',
    ...scoped(['#order-form']),
    effect: { external: true, effectKey: `order:${task.id}`, ...(reference ? { externalIdempotencyKey: reference } : {}) },
    completion: { completedWhen: [{ kind: 'url-prefix', value: `${task.origin}/orders/` }] },
  }),
  download: (target, options, { base, actionId, scoped }) => ({ ...base, actionId: actionId('download'), kind: 'download', ...scoped(['#invoice']) }),
});

const procurementFawnProfile = Object.freeze({
  views: FAWN_VIEWS,
  parsers: FAWN_PARSERS,
  actions: FAWN_ACTIONS,
  results: {
    place: (record) => ({ orderId: orderIdOf(record) }),
    download: (record) => ({ sha256: record.evidence.effect.sha256 }),
  },
  interrupted: (task) => ({ effectKey: `order:${task.id}`, idFrom: orderIdOf }),
});


// Playwright agent tooling: parsers of the page-wide agent snapshot.
const ITEM = /^\s*- text: (.+?) \$(\d+)\.(\d{2})(?: (\d+) in stock| (out of stock))?$/;
const BUTTON = /^\s*- button "([^"]+)" (?:\[[^\]]+\] )*\[ref=(e\d+)\]/;
const TEXTBOX = /^\s*- textbox "([^"]+)" (?:\[[^\]]+\] )*\[ref=(e\d+)\](?:: (.*))?$/;
const LINK = /^\s*- link "([^"]+)" \[ref=(e\d+)\]/;
const HEADING = /^\s*- heading "([^"]+)"/;
const ORDER_ROW = /Order (\d+): (.+?) to (.+?); reference (.+?)"?$/;

/** Pairs each "- text: Name $p ..." line with the button that follows it. */
function itemsWithButtons(lines, buttonName) {
  const found = [];
  lines.forEach((line, index) => {
    const item = ITEM.exec(line);
    if (!item) return;
    const button = BUTTON.exec(lines[index + 1] ?? '');
    if (!button || button[1] !== buttonName) return;
    found.push({
      name: item[1],
      price: Number(item[2]) * 100 + Number(item[3]),
      stock: item[5] ? 0 : Number(item[4] ?? 0),
      ref: button[2],
    });
  });
  return found;
}

const PLAYWRIGHT_PARSERS = Object.freeze({
  catalog: (lines) => ({ items: itemsWithButtons(lines, 'Add to cart') }),
  cart: (lines) => ({ lines: itemsWithButtons(lines, 'Remove') }),
  checkout: (lines) => {
    const field = (name) => {
      const line = lines.map((candidate) => TEXTBOX.exec(candidate)).find((match) => match?.[1] === name);
      return line ? { ref: line[2], value: line[3] ?? '' } : null;
    };
    const place = lines.map((line) => BUTTON.exec(line)).find((match) => match?.[1] === 'Place order');
    return { address: field('Address'), reference: field('Reference'), place: place ? { ref: place[2] } : null };
  },
  confirmation: (lines) => {
    const heading = lines.map((line) => HEADING.exec(line)).find(Boolean)?.[1] ?? '';
    const link = lines.map((line) => LINK.exec(line)).find((match) => match?.[1] === 'Download invoice');
    return { orderId: Number(/Order (\d+) placed/.exec(heading)?.[1]) || null, invoice: link ? { ref: link[2] } : null, heading, lines };
  },
  orders: (lines) => ({
    found: lines.some((line) => HEADING.exec(line)?.[1] === 'Orders'),
    orders: lines.map((line) => ORDER_ROW.exec(line)).filter(Boolean)
      .map(([, id, items, address, reference]) => ({ id: Number(id), items, address, reference })),
  }),
});


/**
 * The order call began but its result was lost. Check the page the browser is on, then the
 * application's order list; with an idempotency reference a resubmission is safe; otherwise
 * the outcome is unknown and goes to human review.
 */
async function resolveInterruptedOrder(agent, task, progress) {
  const current = PLAYWRIGHT_PARSERS.confirmation((await agent.snapshot()).full.split('\n'));
  if (current.orderId && current.lines.some((line) => line.includes(`Ship to: ${progress.address};`))) {
    return { id: current.orderId };
  }
  await agent.navigate(`${task.origin}/orders`);
  const list = await agent.view('orders');
  if (list.found) {
    const match = list.orders.find((order) => order.address === progress.address
      && order.reference === (progress.reference ?? 'none'));
    return match ? { id: match.id } : { retry: true };
  }
  if (progress.reference) return { retry: true };
  return { humanReview: true, reason: 'order outcome unknown: no confirmation on the page, no order list, no idempotency' };
}

const PLAYWRIGHT_ACTS = Object.freeze({
  add: (agent, target) => agent.tool('click', { ref: target.ref }, { consequential: true }),
  remove: (agent, target) => agent.tool('click', { ref: target.ref }, { consequential: true }),
  fill: (agent, target, { value }) => agent.tool('fill', { ref: target.ref, value }, { consequential: true }),
  download: (agent, target) => agent.tool('download', { ref: target.ref }, { consequential: true }),
  async place(agent, target) {
    agent.requireAllowed((await agent.tool('formAction')).action);
    const placed = await agent.tool('click', { ref: target.ref }, { consequential: true });
    return { orderId: Number(/\/orders\/(\d+)/.exec(placed.url)?.[1]) || null };
  },
});

const procurementPlaywrightProfile = Object.freeze({
  parsers: PLAYWRIGHT_PARSERS,
  act: PLAYWRIGHT_ACTS,
  resolveInterrupted: resolveInterruptedOrder,
});

export { procurementFawnProfile, procurementPlaywrightProfile };
