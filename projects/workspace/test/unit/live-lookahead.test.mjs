import assert from 'node:assert/strict';
import test from 'node:test';
import { OBSERVATION_SCHEMA } from '../../src/client/branch-verifier.js';
import { CERTIFICATE_SCHEMA, evaluateLiveLookahead, extractMinimalReadRoles } from '../../src/client/live-lookahead.js';
import { collectObservedFacts, learnRepairBoundary } from '../../src/client/repair-boundary.js';

const BINDING = 'opbind-v1:' + 'a'.repeat(64);
const page = (change = {}) => {
  const dirty = change.dirty ?? [];
  return { alerts: [], statuses: [], truncated: false, ...change, dirty, values: change.values ?? dirty.map(n => [n, 'd1']) };
};
const branchText = ({ ended = 'finished', attempts = [], after = {}, before = {}, thrown = null, intents = [] } = {}) => [
  ended,
  ...attempts.map(([attempt, target]) => JSON.stringify({ attempt, target })),
  ...(ended === 'finished' ? [JSON.stringify({ ok: true, value: { schema: OBSERVATION_SCHEMA, before: page(before), after: page(after), thrown, intents, intentsTruncated: false } })] : []),
].join('\n');

const makeResponses = ({ orderQty = 10, quoteStatus = 1, quoteQty = 10, extraNoise = 99 }) => [
  { sameOrigin: true, method: 'GET', transport: 'fetch', status: 200, sourceRole: 'order', json: { totalQty: orderQty } },
  { sameOrigin: true, method: 'GET', transport: 'fetch', status: 200, sourceRole: 'quotation', json: { docstatus: quoteStatus, totalQty: quoteQty } },
  { sameOrigin: true, method: 'GET', transport: 'fetch', status: 200, sourceRole: 'audit_unused', json: { entryCount: extraNoise } },
];

const learnedBoundary = () => learnRepairBoundary({
  intendedEffect: BINDING,
  positive: [
    collectObservedFacts(makeResponses({ orderQty: 10, quoteStatus: 1, quoteQty: 10, extraNoise: 1 })),
    collectObservedFacts(makeResponses({ orderQty: 25, quoteStatus: 1, quoteQty: 25, extraNoise: 2 })),
  ],
  negative: [
    collectObservedFacts(makeResponses({ orderQty: 10, quoteStatus: 0, quoteQty: 10, extraNoise: 1 })),
    collectObservedFacts(makeResponses({ orderQty: 10, quoteStatus: 1, quoteQty: 5, extraNoise: 2 })),
  ],
});

const EXPECT = { attempt: 'fetch', target: 'https://app.test/api/orders/7/confirm', method: 'POST', bodyFields: ['reference'] };
const CLEAN_INTENT = [{ api: 'fetch', target: EXPECT.target, url: EXPECT.target, method: 'POST', body: { kind: 'json', bytes: 22, fields: [['reference', 'aaaa1111bbbb2222']] } }];

test('extractMinimalReadRoles drops unreferenced discovery roles', () => {
  const b = learnedBoundary();
  assert.equal(b.status, 'learned');
  assert.deepEqual(extractMinimalReadRoles(b), ['order', 'quotation']);
});

test('short-circuits at 0 branches when authoritative server facts fail before branching', async () => {
  const b = learnedBoundary();
  let branchesCalled = 0;
  const cert = await evaluateLiveLookahead({
    boundary: b,
    intendedEffect: BINDING,
    candidates: [{ id: 'v1-reuse', kind: 'reuse', action: 'window.saveOrder()', expect: EXPECT }],
    readServerRoles: async roles => ({
      reads: roles.length,
      responses: makeResponses({ orderQty: 10, quoteStatus: 0, quoteQty: 10 }).filter(r => roles.includes(r.sourceRole)),
    }),
    runBranches: async () => { branchesCalled += 1; return {}; },
  });
  assert.equal(cert.schema, CERTIFICATE_SCHEMA);
  assert.equal(cert.decision, 'abstain');
  assert.equal(cert.stage, 'pre-branch-facts');
  assert.equal(cert.reason, 'guard-mismatch');
  assert.equal(cert.branchesRun, 0);
  assert.equal(cert.serverReads, 2);
  assert.equal(branchesCalled, 0);
});

test('emits reuse when v1 candidate succeeds and repair when v1 fails client drift while repair candidate succeeds', async () => {
  const b = learnedBoundary();
  const candidates = [
    { id: 'v1-reuse', kind: 'reuse', action: 'window.oldSave()', expect: EXPECT, fields: ['reference'] },
    { id: 'v2-repair', kind: 'repair', action: 'window.newSave()', expect: EXPECT, fields: ['reference'] },
    { id: 'v2-extra', kind: 'repair', action: 'window.extra()', expect: EXPECT, fields: ['reference'] },
  ];
  const validReader = async roles => ({
    reads: roles.length,
    responses: makeResponses({ orderQty: 10, quoteStatus: 1, quoteQty: 10 }).filter(r => roles.includes(r.sourceRole)),
  });

  // v1 clean -> decision === 'reuse', pruned to top-2 (1 control + 2 candidates = 3 branches)
  const reuseCert = await evaluateLiveLookahead({
    boundary: b,
    intendedEffect: BINDING,
    pruneTopK: 2,
    candidates,
    readServerRoles: validReader,
    runBranches: async ({ candidates: asked }) => {
      assert.equal(asked.length, 2);
      return {
        control: branchText(),
        candidates: [
          { id: 'v1-reuse', text: branchText({ attempts: [['fetch', EXPECT.target]], after: { dirty: ['reference'] }, intents: CLEAN_INTENT }) },
          { id: 'v2-repair', text: branchText({ attempts: [] }) },
        ],
      };
    },
  });
  assert.equal(reuseCert.decision, 'reuse');
  assert.equal(reuseCert.winnerId, 'v1-reuse');
  assert.equal(reuseCert.branchesRun, 3);
  assert.equal(reuseCert.serverReads, 4); // 2 pre + 2 post

  // v1 drifted (adds hidden surcharge field in POST body), v2-repair clean -> decision === 'repair'
  const driftedIntent = [{
    api: 'fetch', target: EXPECT.target, url: EXPECT.target, method: 'POST',
    body: { kind: 'json', bytes: 40, fields: [['reference', 'aaaa1111bbbb2222'], ['surcharge', '9999000011112222']] },
  }];
  const repairCert = await evaluateLiveLookahead({
    boundary: b,
    intendedEffect: BINDING,
    pruneTopK: 2,
    candidates,
    readServerRoles: validReader,
    runBranches: async () => ({
      control: branchText(),
      candidates: [
        { id: 'v1-reuse', text: branchText({ attempts: [['fetch', EXPECT.target]], after: { dirty: ['reference'] }, intents: driftedIntent }) },
        { id: 'v2-repair', text: branchText({ attempts: [['fetch', EXPECT.target]], after: { dirty: ['reference'] }, intents: CLEAN_INTENT }) },
      ],
    }),
  });
  assert.equal(repairCert.decision, 'repair');
  assert.equal(repairCert.winnerId, 'v2-repair');
  assert.deepEqual(
    Object.fromEntries(repairCert.candidateVerdicts.map(r => [r.id, r.verdict])),
    { 'v1-reuse': 'unexpected-body-field', 'v2-repair': 'eligible' },
  );
});

test('blocks TOCTOU server state change caught during post-branch re-attestation', async () => {
  const b = learnedBoundary();
  let callCount = 0;
  const cert = await evaluateLiveLookahead({
    boundary: b,
    intendedEffect: BINDING,
    candidates: [{ id: 'v1-reuse', kind: 'reuse', action: 'window.save()', expect: EXPECT, fields: ['reference'] }],
    readServerRoles: async roles => {
      callCount += 1;
      const quoteStatus = callCount === 1 ? 1 : 2; // Quotation cancelled while branch preview ran!
      return {
        reads: roles.length,
        responses: makeResponses({ orderQty: 10, quoteStatus, quoteQty: 10 }).filter(r => roles.includes(r.sourceRole)),
      };
    },
    runBranches: async () => ({
      control: branchText(),
      candidates: [{ id: 'v1-reuse', text: branchText({ attempts: [['fetch', EXPECT.target]], after: { dirty: ['reference'] }, intents: CLEAN_INTENT }) }],
    }),
  });
  assert.equal(cert.decision, 'abstain');
  assert.equal(cert.stage, 'branch-or-post-attest');
  assert.equal(cert.reason, 'guard-mismatch');
  assert.equal(cert.winnerId, null);
});
