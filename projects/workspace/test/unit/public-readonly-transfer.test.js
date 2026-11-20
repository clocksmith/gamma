import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  attachReadOnlyNetworkGuard,
  createBudgetedReadOnlyPlanner,
  isReadOnlyHttpMethod,
  parseReadOnlyBudgetCeilings,
  startReadOnlyReferenceMirrorServer,
  validateReadOnlyTransferSpec,
} from '../../qualification/public-readonly-transfer.js';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../../..');

assert.equal(isReadOnlyHttpMethod('GET'), true);
assert.equal(isReadOnlyHttpMethod('HEAD'), true);
assert.equal(isReadOnlyHttpMethod('POST'), false);
assert.equal(isReadOnlyHttpMethod('DELETE'), false);

// Reject missing or invalid live spend ceilings
assert.throws(
  () => parseReadOnlyBudgetCeilings({ controlled: false, maxCallsRaw: null, maxCostUsdRaw: '1' }),
  /require explicit --max-calls and --max-cost-usd/,
);
assert.throws(
  () => parseReadOnlyBudgetCeilings({ controlled: false, maxCallsRaw: '10', maxCostUsdRaw: '0.10', maxCallUsdRaw: '0.25' }),
  /not exceeding --max-cost-usd/,
);

// Verify pre-call enforcement of both --max-calls and --max-cost-usd before invoking provider.next()
{
  let providerCalls = 0;
  const ceilings = parseReadOnlyBudgetCeilings({ controlled: false, maxCallsRaw: '2', maxCostUsdRaw: '0.25', maxCallUsdRaw: '0.15' });
  const budgeted = createBudgetedReadOnlyPlanner({
    provider: {
      identity: { model: 'sonnet' },
      next: async () => {
        providerCalls += 1;
        return { tool: 'observe', input: {}, usage: { costUsd: 0.12 } };
      },
    },
    ceilings,
    controlled: false,
  });
  await budgeted.next({});
  assert.equal(providerCalls, 1);
  // Second call would reserve 0.12 + 0.15 = 0.27 > 0.25 -> must throw BEFORE calling provider.next
  await assert.rejects(() => budgeted.next({}), /spend ceiling reached/);
  assert.equal(providerCalls, 1, 'Spend ceiling must stop before invoking provider');
}

{
  let providerCalls = 0;
  const ceilings = parseReadOnlyBudgetCeilings({ controlled: false, maxCallsRaw: '1', maxCostUsdRaw: '2.00', maxCallUsdRaw: '0.15' });
  const budgeted = createBudgetedReadOnlyPlanner({
    provider: {
      identity: { model: 'sonnet' },
      next: async () => {
        providerCalls += 1;
        return { tool: 'observe', input: {}, usage: { costUsd: 0.05 } };
      },
    },
    ceilings,
    controlled: false,
  });
  await budgeted.next({});
  await assert.rejects(() => budgeted.next({}), /call ceiling reached/);
  assert.equal(providerCalls, 1, 'Call ceiling must stop before invoking provider');
}

// Validate checked-in Reploid PR #6 read-only spec (merge commit 7df3c3b63, two files)
const pr6Spec = validateReadOnlyTransferSpec(
  JSON.parse(readFileSync(join(root, 'projects/workspace/qualification/specs/reploid-pr6-readonly.json'), 'utf8')),
);
assert.equal(pr6Spec.entryUrl, 'https://github.com/clocksmith/reploid/pull/6');
assert.equal(pr6Spec.pinnedTargetMetadata.shortMergeCommit, '7df3c3b63');
assert.deepEqual(pr6Spec.pinnedTargetMetadata.changedFiles, ['README.md', 'docs/open-mesh-architecture.md']);
assert.deepEqual(pr6Spec.allowedReadOrigins, ['https://github.com']);

// Reject submit/password/file controls in read-only transfer specs
assert.throws(
  () => validateReadOnlyTransferSpec({
    entryUrl: 'https://example.org/docs',
    fields: [{ slot: 'pw', kind: 'fill', locator: ['textbox', 'Password', 'input', 'password'] }],
    intermediateClicks: [],
    queries: [{ inputs: {}, expectedText: 'ok' }, { inputs: {}, expectedText: 'ok' }],
  }),
  /Forbidden input type/,
);

// Verify network guard blocks POST (both XHR and document form writes) and disallowed origins
const routes = [];
const mockPage = { route: (_pattern, fn) => { routes.push(fn); } };
const guard = attachReadOnlyNetworkGuard(mockPage, 'https://docs.example.org', {
  allowedReadOrigins: ['https://cdn.example.org'],
});
await guard.install();
assert.equal(routes.length, 1);

let continued = 0;
let aborted = 0;
await routes[0]({
  request: () => ({ method: () => 'GET', url: () => 'https://docs.example.org/search?q=1', resourceType: () => 'document' }),
  continue: async () => { continued += 1; },
  abort: async () => { aborted += 1; },
});
await routes[0]({
  request: () => ({ method: () => 'GET', url: () => 'https://cdn.example.org/app.css', resourceType: () => 'stylesheet' }),
  continue: async () => { continued += 1; },
  abort: async () => { aborted += 1; },
});
await routes[0]({
  request: () => ({ method: () => 'POST', url: () => 'https://docs.example.org/submit', resourceType: () => 'document' }),
  continue: async () => { continued += 1; },
  abort: async () => { aborted += 1; },
});
await routes[0]({
  request: () => ({ method: () => 'GET', url: () => 'https://evil.example.net/pixel', resourceType: () => 'image' }),
  continue: async () => { continued += 1; },
  abort: async () => { aborted += 1; },
});
assert.equal(continued, 2);
assert.equal(aborted, 2);
assert.equal(guard.blockedRequests.length, 2);
assert.equal(guard.blockedDocumentWrites.length, 1);
assert.equal(guard.getDispatchedWriteRequests(), 0);

const mirror = await startReadOnlyReferenceMirrorServer();
try {
  const getRes = await fetch(`${mirror.origin}/docs?q=adapter&section=Specs`);
  assert.equal(getRes.status, 200);
  assert.match(await getRes.text(), /WebGPU Adapter Limits/);
  const postRes = await fetch(`${mirror.origin}/newsletter`, { method: 'POST' });
  assert.equal(postRes.status, 405);
  assert.equal(mirror.getServerWriteHits(), 1);
} finally {
  await mirror.close();
}

console.log('ok: public read-only transfer budget enforcement, PR #6 spec, POST/cross-origin network guard and reference mirror');
