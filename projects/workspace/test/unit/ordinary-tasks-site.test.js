// Unit checks for the Track C ordinary browser task suite and independent oracles.

import assert from 'node:assert/strict';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  buildOrdinaryTaskSpecs,
  computeDockQuote,
  computeExpenseTier,
  computeMatchingInvoices,
  computeMatchingRelease,
  startOrdinaryTasksServer,
} from '../../qualification/ordinary-tasks-site.js';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../../../..');
const SIMULATTE_REPO = resolve(ROOT, '../simulatte');

const specs = buildOrdinaryTaskSpecs();
assert.equal(specs.length, 6, 'expected six ordinary tasks');
const categories = new Set(specs.map((s) => s.category));
assert.deepEqual(
  [...categories].sort(),
  ['form-fill', 'multi-page-nav', 'search-extract'],
  'expected coverage across all three ordinary task categories',
);

for (const spec of specs) {
  assert.equal(spec.learnInputs.length, 3, `${spec.id} requires 3 learn inputs`);
  assert.equal(spec.evalInputs.length, 3, `${spec.id} requires 3 eval inputs`);
  for (let r = 0; r < 3; r += 1) {
    assert.notDeepEqual(
      spec.learnInputs[r],
      spec.evalInputs[r],
      `${spec.id} repeat ${r} learn and eval inputs must differ`,
    );
  }
}

assert.equal(computeExpenseTier('Software', '149'), 'auto-eligible');
assert.equal(computeExpenseTier('Travel', '620'), 'manager-review');
assert.equal(computeExpenseTier('Hardware', '280'), 'manager-review');

const inv = computeMatchingInvoices({ vendorQuery: 'Beacon', status: 'Open', quarter: 'Q2' });
assert.deepEqual(inv.ids, ['INV-2044', 'INV-2045']);
assert.equal(inv.formattedTotal, '$3000.00');

const quote = computeDockQuote({ quantity: '4', shippingTier: 'Two-day' });
assert.equal(quote.total, '$1024.00');

const rel = computeMatchingRelease({ channel: 'LTS', subsystem: 'router' });
assert.equal(rel.version, 'v4.6.9-lts');

const server = await startOrdinaryTasksServer({ simulatteRepo: SIMULATTE_REPO });
try {
  const url = server.createSession('unit-check-1', 'application');
  const html = await (await fetch(url)).text();
  assert.ok(html.includes('Engineer Application'));
  assert.equal(server.getSubmissions('unit-check-1'), 0);

  const postRes = await fetch(`${server.origin}/tasks/unit-check-1/submit`, { method: 'POST', body: 'x=1' });
  assert.equal(postRes.status, 200);
  assert.equal(server.getSubmissions('unit-check-1'), 1);

  const lucydIds = server.expectedLucydIds('queue');
  assert.ok(lucydIds.length >= 3, 'expected committed Simulatte catalog matches for queue');
} finally {
  await server.close();
}

console.log('ok: ordinary browser task suite routes, independent oracles and submission counters');
