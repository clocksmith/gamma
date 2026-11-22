import assert from 'node:assert/strict';
import test from 'node:test';
import {
  evaluateHeldOutRouteWithFrozenBundle,
  freezeQualificationRepairBundle,
  runFiveArmRepairBoundaryComparison,
  verifyCanonicalSingleStepRepair,
} from '../../qualification/workflow-generalization/repair-boundary-qualification.mjs';
import { computeOpenProjectOperationBinding } from '../../qualification/workflow-generalization/stage2-upstream-contract-probe.mjs';

const resp = (role, json, status = 200) => ({
  sameOrigin: true,
  method: 'GET',
  transport: 'xhr',
  status,
  sourceRole: role,
  json,
});

const preUpgradeSteps = [
  { kind: 'fill', role: 'textbox', label: 'Review Note', slot: 'note', authority: 'ordinary-ui' },
  { kind: 'click', role: 'button', label: 'Submit Approval', slot: null, authority: 'reviewed-write' },
];

const validSingleStepRepair = {
  authorityScope: 'org/openproject-local',
  steps: [
    { kind: 'fill', role: 'textbox', label: 'Review Note', slot: 'note', authority: 'ordinary-ui' },
    { kind: 'click', role: 'button', label: 'Confirm Approved Terms', slot: null, authority: 'reviewed-write' },
  ],
};

const effectContract = {
  schema: 'approved-effect-contract/v1',
  endpoint: 'PATCH /api/v3/work_packages/{id}',
};

test('enforces single-shared-step semantic diff and unchanged authority scope', () => {
  const ok = verifyCanonicalSingleStepRepair({
    preUpgradeSteps,
    preUpgradeAuthorityScope: 'org/openproject-local',
    proposedRepair: validSingleStepRepair,
  });
  assert.equal(ok.changedStepIndex, 1);

  assert.throws(
    () =>
      verifyCanonicalSingleStepRepair({
        preUpgradeSteps,
        preUpgradeAuthorityScope: 'org/openproject-local',
        proposedRepair: { ...validSingleStepRepair, authorityScope: 'org/escalated' },
      }),
    err => err.code === 'repair-authority-changed',
  );

  assert.throws(
    () =>
      verifyCanonicalSingleStepRepair({
        preUpgradeSteps,
        preUpgradeAuthorityScope: 'org/openproject-local',
        proposedRepair: {
          authorityScope: 'org/openproject-local',
          steps: [
            { kind: 'fill', role: 'textbox', label: 'Changed 1', slot: 'note', authority: 'ordinary-ui' },
            { kind: 'click', role: 'button', label: 'Changed 2', slot: null, authority: 'reviewed-write' },
          ],
        },
      }),
    err => err.code === 'non-single-step-repair',
  );
});

test('freezes 4 separate records, instantiates per-record held-out opbind-v1, and scores all 5 arms', () => {
  const teachingBinding = computeOpenProjectOperationBinding({
    workPackageId: '10',
    preCommitLockVersion: 2,
    expectedActorHref: '/api/v3/users/101',
    intendedChanges: { statusHref: '/api/v3/statuses/2' },
    clientOperationId: 'teach-op-10',
  });

  // Two disposable positives (`PT8H` and `PT16H`) + one superseded-terms negative (`PT16H` vs `PT8H`)
  // isolate the unique relational minimum `approval:/estimatedTime === record:/estimatedTime`:
  const frozen = freezeQualificationRepairBundle({
    preUpgradeSteps,
    preUpgradeAuthorityScope: 'org/openproject-local',
    proposedRepair: validSingleStepRepair,
    effectContract,
    teachingReferenceBinding: teachingBinding,
    positiveExamples: [
      {
        recordId: '10',
        responses: [
          resp('record', { id: 10, lockVersion: 2, estimatedTime: 'PT8H' }),
          resp('approval', { id: 1, lockVersion: 1, estimatedTime: 'PT8H' }),
        ],
      },
      {
        recordId: '11',
        responses: [
          resp('record', { id: 11, lockVersion: 4, estimatedTime: 'PT16H' }),
          resp('approval', { id: 2, lockVersion: 3, estimatedTime: 'PT16H' }),
        ],
      },
    ],
    counterexamples: [
      {
        recordId: '12',
        label: 'superseded-approval-terms',
        responses: [
          resp('record', { id: 12, lockVersion: 2, estimatedTime: 'PT16H' }),
          resp('approval', { id: 1, lockVersion: 1, estimatedTime: 'PT8H' }),
        ],
      },
    ],
  });

  assert.equal(frozen.learnedGuard.status, 'learned');
  assert.deepEqual(frozen.learnedGuard.guard, [
    { kind: 'equals-field', left: 'approval:/estimatedTime', right: 'record:/estimatedTime' },
  ]);

  // Refuses reusing training recordId `'10'` in held-out evaluation:
  assert.throws(
    () =>
      evaluateHeldOutRouteWithFrozenBundle(frozen, {
        recordId: '10',
        actorHref: '/api/v3/users/101',
        preCommitLockVersion: 2,
        clientOperationId: 'teach-op-10',
        intendedChanges: { statusHref: '/api/v3/statuses/2' },
        responses: [
          resp('record', { lockVersion: 2, estimatedTime: 'PT8H' }),
          resp('approval', { lockVersion: 1, estimatedTime: 'PT8H' }),
        ],
      }),
    err => err.code === 'training-record-reused-in-holdout',
  );

  const heldOutRoutes = [
    {
      recordId: '21',
      actorHref: '/api/v3/users/101',
      preCommitLockVersion: 5,
      clientOperationId: 'holdout-op-21',
      intendedChanges: { statusHref: '/api/v3/statuses/2' },
      groundTruthValidTransfer: true,
      serverRejectsAtCommit: false,
      responses: [
        resp('record', { id: 21, lockVersion: 5, estimatedTime: 'PT24H' }),
        resp('approval', { id: 3, lockVersion: 2, estimatedTime: 'PT24H' }),
      ],
    },
    {
      recordId: '22',
      actorHref: '/api/v3/users/101',
      preCommitLockVersion: 3,
      clientOperationId: 'holdout-op-22',
      intendedChanges: { statusHref: '/api/v3/statuses/2' },
      groundTruthValidTransfer: false,
      // Separate-entity parent ABA is not rejected by stock OpenProject child PATCH alone:
      serverRejectsAtCommit: false,
      responses: [
        resp('record', { id: 22, lockVersion: 3, estimatedTime: 'PT12H' }),
        resp('approval', { id: 3, lockVersion: 2, estimatedTime: 'PT8H' }),
      ],
    },
  ];

  const rows = runFiveArmRepairBoundaryComparison({
    frozenBundle: frozen,
    heldOutRoutes,
    handwrittenGuardLoc: 14,
    handwrittenAuthoringMinutes: 12,
    conventionalScriptLoc: 38,
    conventionalScriptAuthoringMinutes: 20,
    handwrittenGuardFn: obs => {
      if (obs.status !== 'observed') return { status: 'abstain', fieldObservations: 0 };
      return {
        status:
          obs.facts['approval:/estimatedTime'] === obs.facts['record:/estimatedTime']
            ? 'eligible-for-review'
            : 'abstain',
        fieldObservations: 2,
      };
    },
  });

  const byArm = Object.fromEntries(rows.map(r => [r.arm, r]));
  assert.equal(byArm['shared-repair-without-learned-guard'].committedWrongEffects, 1);
  assert.equal(byArm['conventional-script'].committedWrongEffects, 1);
  assert.equal(byArm['always-replan'].planningCalls, 6);
  assert.equal(byArm['learned-selective-reuse'].verifiedValidTransfers, 1);
  assert.equal(byArm['learned-selective-reuse'].unnecessaryAbstentions, 0);
  assert.equal(byArm['learned-selective-reuse'].attemptedWrongTransfers, 0);
  assert.equal(byArm['learned-selective-reuse'].committedWrongEffects, 0);
  assert.equal(byArm['learned-selective-reuse'].planningCalls, 0);
  assert.equal(byArm['learned-selective-reuse'].integrationLoc, 0);
  assert.equal(byArm['handwritten-guard'].integrationLoc, 14);
});
