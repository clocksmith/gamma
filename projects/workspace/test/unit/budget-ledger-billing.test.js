import assert from 'node:assert/strict';
import { createDispatchBudgetLedger } from '../../qualification/budget-ledger.js';

// Fake stateful billing backend simulating concurrent flight, partial-billed retries, and settlement
function createFakeBillingBackend({ defaultCostUsd = 0.06, delayMs = 15, failQueue = [] } = {}) {
  let providerInvocations = 0;
  let queueCursor = 0;
  let totalChargedByBackendUsd = 0;
  const ledgerRows = [];

  return {
    getStats: () => ({
      providerInvocations,
      totalChargedByBackendUsd: Number(totalChargedByBackendUsd.toFixed(6)),
      ledgerRows,
    }),
    provider: {
      identity: { model: 'claude-sonnet-5-5' },
      async next(ctx) {
        const directive = failQueue[queueCursor] ?? null;
        queueCursor += 1;
        if (directive?.neverDispatched) {
          throw Object.assign(Error('local spawn failed before network'), { neverDispatched: true });
        }
        const idx = providerInvocations;
        providerInvocations += 1;
        await new Promise(r => setTimeout(r, delayMs));
        if (directive?.failWithCostUsd !== undefined) {
          totalChargedByBackendUsd += directive.failWithCostUsd;
          ledgerRows.push({ idx, status: 'failed-billed', costUsd: directive.failWithCostUsd });
          throw Object.assign(Error('provider stream truncated'), {
            usage: { costUsd: directive.failWithCostUsd, models: ['claude-sonnet-5-5'] },
          });
        }
        const cost = directive?.costUsd ?? ctx?.costUsd ?? defaultCostUsd;
        totalChargedByBackendUsd += cost;
        ledgerRows.push({ idx, status: 'ok', costUsd: cost });
        return {
          tool: 'observe',
          input: {},
          usage: { costUsd: cost, models: ['claude-sonnet-5-5'] },
        };
      },
    },
  };
}

// 1. Default $8.00 / 240-call / $0.15-per-call policy enforcement & concurrent Promise.all safety
{
  const backend = createFakeBillingBackend({ defaultCostUsd: 0.08, delayMs: 25 });
  // Cap at $0.45 with $0.15/call reservation -> at most 3 concurrent calls can reserve before reconciliation!
  const ledger = createDispatchBudgetLedger({
    controlled: false,
    maxCalls: 240,
    maxCostUsd: 0.45,
    maxCallUsd: 0.15,
  });
  const planner = ledger.wrapPlanner({ provider: backend.provider, arm: 'fawn-graph', runName: 'conc-1' });

  const outcomes = await Promise.allSettled(
    Array.from({ length: 8 }, () => planner.next({})),
  );
  const fulfilled = outcomes.filter(o => o.status === 'fulfilled');
  const rejected = outcomes.filter(o => o.status === 'rejected');
  assert.equal(fulfilled.length, 3, 'Only 3 concurrent $0.15 reservations fit inside $0.45');
  assert.equal(rejected.length, 5, 'Remaining 5 concurrent calls must reject before touching backend');
  assert.equal(backend.getStats().providerInvocations, 3, 'Backend never invoked for rejected reservations');

  // After those 3 settle at $0.08 each ($0.24 reconciled), $0.21 headroom remains -> 1 more $0.15 reservation fits!
  const snapAfterWave1 = ledger.snapshot();
  assert.equal(snapAfterWave1.reconciledBilledUsd, 0.24);
  assert.equal(snapAfterWave1.reservedUpperUsd, 0.24);

  await planner.next({});
  assert.equal(backend.getStats().providerInvocations, 4);
  assert.equal(ledger.snapshot().reconciledBilledUsd, Number(backend.getStats().totalChargedByBackendUsd.toFixed(6)));
}

// 2. Retries: never-dispatched failure releases slot; partially-billed failure reconciles exact charge
{
  const backend = createFakeBillingBackend({
    defaultCostUsd: 0.05,
    delayMs: 5,
    failQueue: [
      { neverDispatched: true },
      { failWithCostUsd: 0.03 },
      null,
    ],
  });
  const ledger = createDispatchBudgetLedger({
    controlled: false,
    maxCalls: 2,
    maxCostUsd: 8.0,
    maxCallUsd: 0.15,
  });
  const planner = ledger.wrapPlanner({ provider: backend.provider, arm: 'fawn-graph', runName: 'retry-1' });

  // Attempt 1: neverDispatched -> releases call slot
  await assert.rejects(() => planner.next({}), /local spawn failed/);
  assert.equal(ledger.snapshot().activeCallsCount, 0);
  assert.equal(ledger.snapshot().reconciledBilledUsd, 0);

  // Attempt 2: failed mid-stream with $0.03 charge -> consumes 1 call slot and $0.03
  await assert.rejects(() => planner.next({}), /provider stream truncated/);
  assert.equal(ledger.snapshot().activeCallsCount, 1);
  assert.equal(ledger.snapshot().reconciledBilledUsd, 0.03);
  assert.equal(ledger.snapshot().retryCount, 2);

  // Attempt 3: succeeds at $0.05 -> consumes 2nd call slot ($0.08 total matching backend!)
  await planner.next({});
  assert.equal(ledger.snapshot().activeCallsCount, 2);
  assert.equal(ledger.snapshot().reconciledBilledUsd, 0.08);
  assert.equal(backend.getStats().totalChargedByBackendUsd, 0.08);

  // Attempt 4: call ceiling (2) now exhausted -> rejects before backend
  await assert.rejects(() => planner.next({}), err => err.code === 'call-ceiling-exhausted');
  assert.equal(backend.getStats().providerInvocations, 2);
}

// 3. Per-arm equal $4.00 / 120-call split prevents one arm from starving the other inside $8.00 / 240
{
  const backend = createFakeBillingBackend({ defaultCostUsd: 0.10, delayMs: 2 });
  const ledger = createDispatchBudgetLedger({
    controlled: false,
    maxCalls: 240,
    maxCostUsd: 8.0,
    maxCallUsd: 0.15,
    perArmCeilings: {
      'fawn-graph': { maxCalls: 2, maxCostUsd: 4.0 },
      'stock-reusable-parts': { maxCalls: 2, maxCostUsd: 4.0 },
    },
  });
  const fawnP = ledger.wrapPlanner({ provider: backend.provider, arm: 'fawn-graph' });
  const stockP = ledger.wrapPlanner({ provider: backend.provider, arm: 'stock-reusable-parts' });
  await fawnP.next({});
  await fawnP.next({});
  await assert.rejects(() => fawnP.next({}), err => err.code === 'arm-call-ceiling-exhausted');
  // Stock arm still has its full independent quota
  await stockP.next({});
  assert.equal(ledger.snapshot().armReconciledUsd['fawn-graph'], 0.2);
  assert.equal(ledger.snapshot().armReconciledUsd['stock-reusable-parts'], 0.1);
}

console.log('ok: dispatch budget ledger concurrent reservations, retries, exhaustion and fake-billing reconciliation');
