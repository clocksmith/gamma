// PII-free, synthetic structural histories. No live recipes or dispatch.
import assert from 'node:assert/strict';

const principal = { workspaceId: 'corpus-qualification', clientId: 'fixture', role: 'member' };
const h = value => value.repeat(64);
const click = (before, after, label, elapsedMs) => ({
  beforeOutline: h(before), afterOutline: h(after), kind: 'click',
  locator: ['button', label, 'button', ''], elapsedMs,
});
const fill = (before, after, label, slot) => ({
  beforeOutline: h(before), afterOutline: h(after), kind: 'fill',
  locator: ['textbox', label, 'input', 'text'], slot, elapsedMs: 10,
});
const next = click('a', 'b', 'Continue', 10);
const quick = click('a', 'd', 'Direct', 5);
const slow = [click('a', 'c', 'Detour', 20), click('c', 'd', 'Return', 20)];
const cases = [
  { id: 'linear', histories: [[next, click('b', 'c', 'Review', 11)]] },
  { id: 'weighted-repeat', histories: [[next], [{ ...next, elapsedMs: 48 }], [{ ...next, elapsedMs: 37 }]] },
  { id: 'branch-and-slot', slots: ['fixture-slot'], histories: [
    [fill('a', 'b', 'Field', 'fixture-slot'), click('b', 'd', 'Review', 11)],
    [click('a', 'c', 'Skip', 20), click('c', 'd', 'Review', 20)],
  ] },
  { id: 'contracted-loop', histories: [[next, click('b', 'a', 'Back', 9), quick]] },
  { id: 'legacy-prunes-detour', histories: [[quick], slow] },
  { id: 'legacy-prunes-then-reweights', histories: [[quick], slow,
    slow.map(step => ({ ...step, elapsedMs: 1 }))] },
  { id: 'legacy-lag-negative', histories: [[next], [click('a', 'd', 'Alternative', 11)]],
    legacyLagAt: 1 },
];

export async function qualifyRecipeGenerationCorpus(engine) {
  const results = [];
  for (const { id, histories, slots = [], legacyLagAt = -1 } of cases) {
    const scope = { origin: 'https://corpus.fixture.example', template: id };
    const checkpoints = [];
    for (const [index, steps] of histories.entries()) {
      const trace = { ...scope, submissionId: id + '-' + index, verificationId: 'review-fixture',
        reviewVerified: true, steps };
      const { acceptanceSequence } = await engine.acceptTrace(principal, trace);
      assert.equal(acceptanceSequence, index + 1);
      const legacyIngested = index !== legacyLagAt;
      const legacyReceipt = legacyIngested ? await engine.ingestTrace(principal, trace) : null;
      const published = await engine.compactAcceptedWorkspace(principal, scope, {
        expectedGeneration: index, inputWatermark: acceptanceSequence,
      });
      const probes = [];
      for (const availableSlots of slots.length ? [[], slots] : [[]]) {
        const request = { ...scope, currentOutline: h('a'), availableSlots };
        const baseline = await engine.resolveRecipe(principal, request);
        const comparison = await engine.compareAcceptedWorkspace(principal, request, {
          generation: published.generation, legacyRevision: baseline.revision, legacyDagDigest: baseline.dagDigest,
        });
        assert.deepEqual(await engine.resolveRecipe(principal, request), baseline);
        assert.equal(comparison.status, legacyIngested ? 'match' : 'mismatch', id + ' generation ' + published.generation);
        if (!legacyIngested) assert.ok(comparison.differences.includes('dag'));
        probes.push({ slotCount: availableSlots.length, status: comparison.status,
          differences: comparison.differences });
      }
      const legacyDetourEdgesRemoved = legacyReceipt?.reduction?.detourEdgesRemoved ?? null;
      if (id.startsWith('legacy-prunes') && index === 1) assert.ok(legacyDetourEdgesRemoved > 0);
      checkpoints.push({ generation: published.generation, legacyIngested, legacyDetourEdgesRemoved, probes });
    }
    results.push({ case: id, checkpoints });
  }
  return results;
}
