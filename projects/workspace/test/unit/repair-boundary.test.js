import assert from 'node:assert/strict';
import {
  compareSelectiveRepairBaselines,
  createAndFreezeRepairBoundary,
  evaluateRepairBoundary,
  extractRawFactCatalogFromHttpTrace,
} from '../../src/client/repair-boundary.js';

// 1. Pre-cooked boolean oracle keys (`repairIsValid`, `canTransfer`, etc.) are rejected:
{
  assert.throws(
    () =>
      extractRawFactCatalogFromHttpTrace([
        {
          method: 'GET',
          url: 'http://op.local/api/v3/work_packages/10',
          status: 200,
          body: { id: 10, lockVersion: 3, repairIsValid: true },
        },
      ]),
    err => err.code === 'forbidden-oracle-fact-key',
  );
}

// Helper building realistic OpenProject-shaped GET traces (target WP + linked approval packet + activities):
function makeOpenProjectRouteTrace({
  wpId,
  wpEstimatedTime,
  wpLockVersion = 2,
  wpStatusHref = '/api/v3/statuses/2',
  approvalEstimatedTime,
  approvalLockVersion = 1,
  approvalStatusHref = '/api/v3/statuses/2',
  approvalHttpStatus = 200,
}) {
  return [
    {
      method: 'GET',
      url: `http://op.local/api/v3/work_packages/${wpId}`,
      roleTag: 'work_package',
      status: 200,
      body: {
        id: wpId,
        subject: `Purchase Review ${wpId}`,
        lockVersion: wpLockVersion,
        estimatedTime: wpEstimatedTime,
        _links: {
          status: { href: wpStatusHref },
          parent: { href: '/api/v3/work_packages/1' },
        },
      },
    },
    {
      method: 'GET',
      url: 'http://op.local/api/v3/work_packages/1',
      roleTag: 'approval_packet',
      status: approvalHttpStatus,
      body:
        approvalHttpStatus === 200
          ? {
              id: 1,
              subject: 'Human Approval Packet',
              lockVersion: approvalLockVersion,
              estimatedTime: approvalEstimatedTime,
              _links: { status: { href: approvalStatusHref } },
            }
          : null,
    },
    {
      method: 'GET',
      url: `http://op.local/api/v3/work_packages/${wpId}/activities`,
      roleTag: 'activities',
      status: 200,
      body: {
        _embedded: {
          elements: [
            { id: 1, version: 1, comment: { raw: 'Created' }, details: [] },
            {
              id: 2,
              version: 2,
              comment: { raw: 'Routed to review' },
              details: [{ format: 'custom', raw: `Status changed to ${wpStatusHref}` }],
            },
          ],
        },
      },
    },
  ];
}

// 2. Teach from 1 positive repair + 1 superseded-terms near miss, freeze, and test unseen routes:
{
  const boundary = createAndFreezeRepairBoundary({
    moduleId: 'openproject-v14-final-approve-screen',
    proposedRepair: {
      repairedOnRouteId: 'standard-route-r1',
      domDigest: 'op14-approve-modal-v2',
      steps: [
        { kind: 'click', label: 'Open Approval Tab' },
        { kind: 'click', label: 'Confirm Approved Terms' },
      ],
    },
    intendedEffect: {
      operationBindingSchema: 'opbind-v1',
      nonWaivableByModel: true,
      targetEndpoint: 'PATCH /api/v3/work_packages/{id}',
    },
    positiveTraces: [
      {
        id: 'pos-standard-pt8h',
        routeId: 'standard-route-r1',
        httpExchanges: makeOpenProjectRouteTrace({
          wpId: 10,
          wpEstimatedTime: 'PT8H',
          approvalEstimatedTime: 'PT8H',
        }),
      },
    ],
    counterexampleTraces: [
      {
        id: 'near-miss-superseded-terms',
        routeId: 'standard-route-superseded',
        failureKind: 'superseded-approval-terms',
        httpExchanges: makeOpenProjectRouteTrace({
          wpId: 11,
          wpEstimatedTime: 'PT16H',
          approvalEstimatedTime: 'PT8H',
        }),
      },
    ],
  });

  assert.equal(boundary.learnRepairs, false);
  assert.equal(boundary.discriminatingGuard.status, 'separated');
  assert.equal(boundary.discriminatingGuard.arity, 1);
  // Relational equality (`approval_packet.estimatedTime === work_package.estimatedTime`) beats literal `'PT8H'`:
  assert.deepEqual(boundary.discriminatingGuard.clauses, [
    {
      kind: 'eq_path',
      leftPath: 'approval_packet.estimatedTime',
      rightPath: 'work_package.estimatedTime',
    },
  ]);

  // Unseen sibling route U1 (expedited route with a NEVER-SEEN budget `PT24H` matching its `PT24H` approval):
  const u1 = evaluateRepairBoundary(
    boundary,
    makeOpenProjectRouteTrace({
      wpId: 21,
      wpEstimatedTime: 'PT24H',
      approvalEstimatedTime: 'PT24H',
    }),
  );
  assert.equal(u1.decision, 'reuse_repair');
  assert.equal(u1.allowReuse, true);
  assert.equal(u1.commitContract.nonWaivableByModel, true);

  // Unseen look-alike route U2 (identical DOM, but approval is for superseded `PT8H` while WP asks `PT12H`):
  const u2 = evaluateRepairBoundary(
    boundary,
    makeOpenProjectRouteTrace({
      wpId: 22,
      wpEstimatedTime: 'PT12H',
      approvalEstimatedTime: 'PT8H',
    }),
  );
  assert.equal(u2.decision, 'refuse_transfer');
  assert.equal(u2.allowReuse, false);
  assert.equal(u2.failedClauses.length, 1);

  // Unseen route U3 where `approval_packet` read fails (`503`) -> MUST abstain without guessing:
  const u3 = evaluateRepairBoundary(
    boundary,
    makeOpenProjectRouteTrace({
      wpId: 23,
      wpEstimatedTime: 'PT8H',
      approvalEstimatedTime: 'PT8H',
      approvalHttpStatus: 503,
    }),
  );
  assert.equal(u3.decision, 'abstain');
  assert.equal(u3.allowReuse, false);
  assert.equal(u3.reason, 'required-fact-unavailable');

  // Tamper check on deserialized boundary copy:
  const tampered = JSON.parse(JSON.stringify(boundary));
  tampered.discriminatingGuard.clauses = [];
  assert.throws(() => evaluateRepairBoundary(tampered, []), err => err.code === 'tampered-repair-boundary');

  // 3. Five-arm selective-repair evaluation on unseen routes:
  const unseenRoutes = [
    {
      id: 'u1-expedited-valid-pt24h',
      validToTransfer: true,
      serverRejectsAtCommit: false,
      httpExchanges: makeOpenProjectRouteTrace({ wpId: 21, wpEstimatedTime: 'PT24H', approvalEstimatedTime: 'PT24H' }),
    },
    {
      id: 'u2-emergency-valid-pt4h',
      validToTransfer: true,
      serverRejectsAtCommit: false,
      httpExchanges: makeOpenProjectRouteTrace({ wpId: 24, wpEstimatedTime: 'PT4H', approvalEstimatedTime: 'PT4H' }),
    },
    {
      id: 'u3-lookalike-superseded-terms',
      validToTransfer: false,
      // Stock OpenProject separate-entity parent ABA does NOT reject child PATCH at commit without a guard!
      serverRejectsAtCommit: false,
      httpExchanges: makeOpenProjectRouteTrace({ wpId: 22, wpEstimatedTime: 'PT12H', approvalEstimatedTime: 'PT8H' }),
    },
    {
      id: 'u4-unavailable-approval-service',
      validToTransfer: false,
      expectsAbstain: true,
      serverRejectsAtCommit: true,
      httpExchanges: makeOpenProjectRouteTrace({
        wpId: 23,
        wpEstimatedTime: 'PT8H',
        approvalEstimatedTime: 'PT8H',
        approvalHttpStatus: 503,
      }),
    },
  ];

  const fiveArms = compareSelectiveRepairBaselines({
    boundary,
    handWrittenGuardLoc: 18,
    scriptMaintainedLoc: 42,
    handWrittenGuard: catalog => {
      if (catalog.unavailableTags.includes('approval_packet')) return { decision: 'abstain', allowReuse: false };
      return {
        decision: 'evaluated',
        allowReuse: catalog.facts['approval_packet.estimatedTime'] === catalog.facts['work_package.estimatedTime'],
      };
    },
    unseenRoutes,
  });

  const byArm = Object.fromEntries(fiveArms.map(r => [r.arm, r]));
  assert.equal(byArm['unguarded-shared-repair'].wrongCommitsApplied, 1);
  assert.equal(byArm['conventional-page-object-script'].wrongCommitsApplied, 1);
  assert.equal(byArm['always-replan'].plannerTurns, 16);
  assert.equal(byArm['learned-selective-reuse'].validTransfersZeroTurns, 2);
  assert.equal(byArm['learned-selective-reuse'].legitimateRoutesNeedlesslyBlocked, 0);
  assert.equal(byArm['learned-selective-reuse'].wrongTransfersAttempted, 0);
  assert.equal(byArm['learned-selective-reuse'].wrongCommitsApplied, 0);
  assert.equal(byArm['learned-selective-reuse'].abstainedCleanly, 1);
  assert.equal(byArm['learned-selective-reuse'].plannerTurns, 0);
  assert.equal(byArm['learned-selective-reuse'].guardLoc, 0);
  assert.equal(byArm['hand-written-guard'].guardLoc, 18);
}

// 4. Unseparated facts -> `RepairBoundary` abstains rather than transferring blindly:
{
  const unseparated = createAndFreezeRepairBoundary({
    moduleId: 'opaque-hidden-rule-module',
    proposedRepair: { steps: [{ kind: 'click', label: 'Submit' }] },
    intendedEffect: { operationBindingSchema: 'opbind-v1', nonWaivableByModel: true },
    positiveTraces: [
      {
        httpExchanges: [
          { method: 'GET', url: 'http://op.local/api/v3/work_packages/5', status: 200, body: { lockVersion: 1, estimatedTime: 'PT8H' } },
        ],
      },
    ],
    counterexampleTraces: [
      {
        httpExchanges: [
          { method: 'GET', url: 'http://op.local/api/v3/work_packages/6', status: 200, body: { lockVersion: 1, estimatedTime: 'PT8H' } },
        ],
      },
    ],
  });
  assert.equal(unseparated.discriminatingGuard.status, 'unseparated');
  const res = evaluateRepairBoundary(unseparated, [
    { method: 'GET', url: 'http://op.local/api/v3/work_packages/7', status: 200, body: { lockVersion: 1, estimatedTime: 'PT8H' } },
  ]);
  assert.equal(res.decision, 'abstain');
  assert.equal(res.allowReuse, false);
}

console.log('repair-boundary: ok');
