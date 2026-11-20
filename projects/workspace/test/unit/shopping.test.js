import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { eligibleOffer, selectShoppingOffer, verifyShoppingQuote, verifyShoppingReceipt, quoteHash } from '../../src/client/shopping-contract.js';
import { ShoppingSession } from '../../src/client/shopping-session.js';
import { PrivateJsonFile } from '../../src/client/private-json-file.js';

const request = { query: 'computer', category: 'computer', minimums: { memoryGb: 32 }, quantity: 1, maxTotalCents: 100000,
  accountId: 'alice', recipient: 'Alice', address: '1 Example Road', postalCode: '10000', shipping: 'Standard' };
const offer = { sku: 'A', category: 'computer', specs: { memoryGb: 32 }, stock: 2, unitCents: 80000, shippingCents: 1000, taxCents: 5000 };
const quote = { sku: 'A', category: 'computer', specs: offer.specs, unitCents: 80000, shippingCents: 1000, taxCents: 5000,
  totalCents: 86000, quantity: 1, accountId: 'alice', recipient: 'Alice', address: '1 Example Road', postalCode: '10000', shipping: 'Standard' };

test('fresh selection rejects cheap incompatible, unavailable and unaffordable products; ties have stable identities', () => {
  const candidates = [{ ...offer, sku: 'B' }, offer, { ...offer, sku: 'cheap', unitCents: 10, specs: { memoryGb: 8 } },
    { ...offer, sku: 'empty', unitCents: 10, stock: 0 }, { ...offer, sku: 'expensive', unitCents: 99999 }];
  assert.equal(selectShoppingOffer(candidates, request).sku, 'A');
  assert.equal(selectShoppingOffer([...candidates].reverse(), request).sku, 'A');
  assert.throws(() => selectShoppingOffer([offer, offer], request), /Ambiguous/);
  assert.throws(() => selectShoppingOffer([], request), /No in-stock/);
  assert.equal(eligibleOffer({ ...offer, unitCents: NaN }, request), false);
});
for (const [field, value] of Object.entries({ sku: 'B', category: 'monitor', specs: { memoryGb: 8 }, totalCents: 85999,
  quantity: 2, unitCents: 80001, shippingCents: 0, taxCents: 0, accountId: 'bob', recipient: 'Bob', address: '2 Example Road', postalCode: '10001', shipping: 'Express' })) {
  test(`quote must bind ${field}`, () => assert.throws(() => verifyShoppingQuote({ ...quote, [field]: value }, offer, request), /differs/));
}
test('receipt binds operation and complete authorized quote, not just a success label', () => {
  const attempt = { operationId: 'op', quoteHash: verifyShoppingQuote(quote, offer, request) };
  assert.equal(verifyShoppingReceipt({ operationId: 'op', orderId: 'order-1', quote }, attempt), true);
  assert.equal(verifyShoppingReceipt({ operationId: 'another', orderId: 'order-1', quote }, attempt), false);
  assert.equal(verifyShoppingReceipt({ operationId: 'op', orderId: 'order-1', quote: { ...quote, totalCents: 1 } }, attempt), false);
  assert.equal(verifyShoppingReceipt(null, attempt), false);
});
test('saved purchase cannot be rerun; recovery performs reads and reconciliation only', async () => {
  const directory = mkdtempSync(join(tmpdir(), 'fawn-shopping-unit-'));
  try {
    const attempts = new PrivateJsonFile(join(directory, 'attempt.json'), { maxBytes: 10000, lockWaitMs: 100, lockRetryMs: 5 });
    const attempt = { version: 1, operationId: 'op', request, origin: 'https://shop.test', siteId: 'site', workspaceId: 'ws',
      actionId: 'action', quote, quoteHash: quoteHash(quote), status: 'unknown' };
    attempts.write(attempt);
    let actions = 0, reconciliations = 0;
    const observation = { url: 'https://shop.test/receipt', isTruncated: false };
    const site = { id: 'site', origin: 'https://shop.test', receiptConditions: () => [{ kind: 'element-present', selector: '#receipt' }],
      read: () => ({ accountId: 'alice', receipt: { operationId: 'op', orderId: 'order-1', quote } }) };
    const driver = { identity: { workspaceId: 'ws' }, observe: async () => observation, act: async () => { actions++; },
      action: async () => ({ isUncertain: true }), reconcile: async () => { reconciliations++; return { isUncertain: false }; } };
    const session = new ShoppingSession({ driver, site, request, mode: 'reuse', attempts, operationId: 'op' });
    await assert.rejects(session.run(), /already exists/);
    assert.equal((await session.recover()).completed, true);
    assert.equal(actions, 0); assert.equal(reconciliations, 1);
    assert.equal(attempts.read(null).status, 'completed');
    const other = new ShoppingSession({ driver, site, request: { ...request, address: 'Another address' }, mode: 'reuse', attempts, operationId: 'op' });
    await assert.rejects(other.recover(), /identity differs/);
  } finally { rmSync(directory, { recursive: true, force: true }); }
});
