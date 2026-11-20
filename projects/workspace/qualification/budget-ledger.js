// Atomic dispatch-time call and spend reservation ledger for Track C1 qualification runners.
//
// Enforces campaign and per-arm call/USD ceilings synchronously BEFORE dispatching any provider
// request, preventing concurrent Promise.all callers from overshooting --max-calls ($8 / 240 / $0.15),
// and reconciles actual billed USD on completion or failed-call retry.

export function validateBudgetCeilings({
  controlled = false,
  maxCalls = 240,
  maxCostUsd = 8,
  maxCallUsd = 0.15,
  perArmCeilings = null,
} = {}) {
  const callsCap = Number.parseInt(String(maxCalls), 10);
  const costCap = Number(maxCostUsd);
  const perCallCap = Number(maxCallUsd);
  if (!Number.isInteger(callsCap) || callsCap < 1) {
    throw Error('--max-calls must be a positive integer');
  }
  if (!Number.isFinite(costCap) || costCap <= 0) {
    throw Error('--max-cost-usd must be a positive finite number');
  }
  if (!Number.isFinite(perCallCap) || perCallCap <= 0 || (!controlled && perCallCap > costCap + 1e-9)) {
    throw Error('--max-call-usd must be a positive finite number not exceeding --max-cost-usd');
  }
  return {
    maxCalls: callsCap,
    maxCostUsd: Number(costCap.toFixed(6)),
    maxCallUsd: Number(perCallCap.toFixed(6)),
    perArmCeilings,
  };
}

export function createDispatchBudgetLedger({
  controlled = false,
  maxCalls = 240,
  maxCostUsd = 8,
  maxCallUsd = 0.15,
  perArmCeilings = null,
  onRecord = null,
} = {}) {
  const ceilings = validateBudgetCeilings({
    controlled,
    maxCalls,
    maxCostUsd,
    maxCallUsd,
    perArmCeilings,
  });

  const calls = [];
  let activeCallsCount = 0;
  let reservedUpperUsd = 0;
  let reconciledBilledUsd = 0;
  let retryCount = 0;
  let exhaustionEvents = 0;
  const armActiveCalls = new Map();
  const armReservedUpperUsd = new Map();
  const armReconciledUsd = new Map();

  function snapshot() {
    return {
      controlled,
      ceilings,
      totalDispatchedCalls: calls.length,
      activeCallsCount,
      retryCount,
      exhaustionEvents,
      reservedUpperUsd: Number(reservedUpperUsd.toFixed(6)),
      reconciledBilledUsd: Number(reconciledBilledUsd.toFixed(6)),
      armReconciledUsd: Object.fromEntries(
        [...armReconciledUsd.entries()].map(([k, v]) => [k, Number(v.toFixed(6))]),
      ),
    };
  }

  function wrapPlanner({ provider, arm = 'default', runName = 'run', itemId = 'item', verifyAttestation = null }) {
    if (!provider || typeof provider.next !== 'function') {
      throw Error('Budget ledger requires a planner provider with next()');
    }
    return {
      identity: provider.identity ?? null,
      async next(...params) {
        // Synchronous reservation check BEFORE first await so concurrent callers serialize atomically.
        if (!controlled) {
          if (activeCallsCount + 1 > ceilings.maxCalls) {
            exhaustionEvents += 1;
            throw Object.assign(Error(`Model call ceiling reached (${ceilings.maxCalls})`), {
              code: 'call-ceiling-exhausted',
            });
          }
          if (reservedUpperUsd + ceilings.maxCallUsd > ceilings.maxCostUsd + 1e-9) {
            exhaustionEvents += 1;
            throw Object.assign(Error(`Campaign spend ceiling reached ($${ceilings.maxCostUsd})`), {
              code: 'spend-ceiling-exhausted',
            });
          }
          const armCap = ceilings.perArmCeilings?.[arm] ?? null;
          if (armCap) {
            const curArmCalls = armActiveCalls.get(arm) ?? 0;
            const curArmUsd = armReservedUpperUsd.get(arm) ?? 0;
            if (curArmCalls + 1 > armCap.maxCalls) {
              exhaustionEvents += 1;
              throw Object.assign(Error(`Per-arm call ceiling reached for ${arm} (${armCap.maxCalls})`), {
                code: 'arm-call-ceiling-exhausted',
              });
            }
            if (curArmUsd + ceilings.maxCallUsd > armCap.maxCostUsd + 1e-9) {
              exhaustionEvents += 1;
              throw Object.assign(Error(`Per-arm spend ceiling reached for ${arm} ($${armCap.maxCostUsd})`), {
                code: 'arm-spend-ceiling-exhausted',
              });
            }
          }
          activeCallsCount += 1;
          reservedUpperUsd += ceilings.maxCallUsd;
          armActiveCalls.set(arm, (armActiveCalls.get(arm) ?? 0) + 1);
          armReservedUpperUsd.set(arm, (armReservedUpperUsd.get(arm) ?? 0) + ceilings.maxCallUsd);
        } else {
          activeCallsCount += 1;
          armActiveCalls.set(arm, (armActiveCalls.get(arm) ?? 0) + 1);
        }

        const startedMs = performance.now();
        const record = {
          callIndex: calls.length + 1,
          run: runName,
          arm,
          itemId,
          startedAt: new Date().toISOString(),
          status: 'started',
          reservedUsd: controlled ? 0 : ceilings.maxCallUsd,
          reconciledUsd: 0,
        };
        calls.push(record);

        try {
          const proposal = await provider.next(...params);
          record.status = 'completed';
          record.tool = proposal?.tool ?? null;
          record.usage = proposal?.usage ?? null;
          if (!controlled && verifyAttestation) {
            verifyAttestation(proposal);
          }
          if (!controlled) {
            const actual = Number.isFinite(record.usage?.costUsd)
              ? record.usage.costUsd
              : ceilings.maxCallUsd;
            if (actual > ceilings.maxCallUsd + 1e-9) {
              throw Object.assign(
                Error(`Single-call spend $${actual} exceeded --max-call-usd $${ceilings.maxCallUsd}`),
                { code: 'per-call-ceiling-exceeded', usage: record.usage },
              );
            }
            record.reconciledUsd = Number(actual.toFixed(6));
            reservedUpperUsd += actual - ceilings.maxCallUsd;
            reconciledBilledUsd += actual;
            armReservedUpperUsd.set(arm, (armReservedUpperUsd.get(arm) ?? 0) + actual - ceilings.maxCallUsd);
            armReconciledUsd.set(arm, (armReconciledUsd.get(arm) ?? 0) + actual);
          }
          return proposal;
        } catch (error) {
          record.status = 'failed';
          record.error = error.message;
          record.usage ??= error.usage ?? null;
          retryCount += 1;
          if (!controlled && record.reconciledUsd === 0) {
            if (error.neverDispatched === true) {
              // Provably never reached provider: release both call slot and USD reservation
              activeCallsCount -= 1;
              reservedUpperUsd -= ceilings.maxCallUsd;
              armActiveCalls.set(arm, (armActiveCalls.get(arm) ?? 1) - 1);
              armReservedUpperUsd.set(arm, (armReservedUpperUsd.get(arm) ?? ceilings.maxCallUsd) - ceilings.maxCallUsd);
              record.reconciledUsd = 0;
            } else if (Number.isFinite(record.usage?.costUsd)) {
              const billed = record.usage.costUsd;
              record.reconciledUsd = Number(billed.toFixed(6));
              reservedUpperUsd += billed - ceilings.maxCallUsd;
              reconciledBilledUsd += billed;
              armReservedUpperUsd.set(arm, (armReservedUpperUsd.get(arm) ?? 0) + billed - ceilings.maxCallUsd);
              armReconciledUsd.set(arm, (armReconciledUsd.get(arm) ?? 0) + billed);
            } else {
              // Unknown provider billing after dispatch: retain conservative maxCallUsd reservation
              record.reconciledUsd = ceilings.maxCallUsd;
              reconciledBilledUsd += ceilings.maxCallUsd;
              armReconciledUsd.set(arm, (armReconciledUsd.get(arm) ?? 0) + ceilings.maxCallUsd);
            }
          }
          throw error;
        } finally {
          record.elapsedMs = Number((performance.now() - startedMs).toFixed(3));
          onRecord?.(calls, snapshot());
        }
      },
    };
  }

  return {
    ceilings,
    calls,
    snapshot,
    wrapPlanner,
  };
}
