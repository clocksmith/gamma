import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import test from 'node:test';
import {
  attachTrustedSameOriginReadObserver,
  evaluateHeldOutRouteWithFrozenBundle,
  freezeQualificationRepairBundle,
  projectOpenProjectHalScalars,
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

const approvedEffectContract = {
  schema: 'approved-effect-contract/v1',
  method: 'PATCH',
  endpointTemplate: '/api/v3/work_packages/{recordId}',
  allowedChangeKeys: ['statusHref', 'estimatedTime'],
  fixedChanges: { statusHref: '/api/v3/statuses/2' },
  factBoundChanges: { estimatedTime: 'approval:/estimatedTime' },
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
});

test('trusted same-origin GET/XHR observer projects OpenProject HAL scalars into collectObservedFacts', async () => {
  const fakePage = new EventEmitter();
  const observer = attachTrustedSameOriginReadObserver(fakePage, {
    allowedOrigin: 'http://127.0.0.1:8080',
    projectJson: projectOpenProjectHalScalars,
    roleMatchers: [
      { role: 'record', matches: p => p === '/api/v3/work_packages/21' },
      { role: 'approval', matches: p => p === '/api/v3/work_packages/3' },
      { role: 'revisions', matches: p => p === '/api/v3/work_packages/21/activities' },
    ],
  });

  const emitResp = ({ url, method = 'GET', resourceType = 'xhr', status = 200, body }) => {
    fakePage.emit('response', {
      url: () => url,
      status: () => status,
      request: () => ({ method: () => method, resourceType: () => resourceType }),
      json: async () => body,
    });
  };

  // Ignored noise: cross-origin, POST, image, and 500:
  emitResp({ url: 'https://evil.example/api/v3/work_packages/21', body: { lockVersion: 999 } });
  emitResp({ url: 'http://127.0.0.1:8080/api/v3/work_packages/21', method: 'PATCH', body: { lockVersion: 888 } });
  emitResp({ url: 'http://127.0.0.1:8080/assets/logo.png', resourceType: 'image', body: {} });

  // Authoritative same-origin GETs:
  emitResp({
    url: 'http://127.0.0.1:8080/api/v3/work_packages/21',
    body: {
      id: 21,
      subject: 'Ignored free text',
      lockVersion: 5,
      estimatedTime: 'PT24H',
      _links: { status: { href: '/api/v3/statuses/2' } },
    },
  });
  emitResp({
    url: 'http://127.0.0.1:8080/api/v3/work_packages/3',
    body: {
      id: 3,
      lockVersion: 2,
      estimatedTime: 'PT24H',
      _links: { status: { href: '/api/v3/statuses/2' } },
    },
  });
  emitResp({
    url: 'http://127.0.0.1:8080/api/v3/work_packages/21/activities',
    transport: 'fetch',
    body: {
      _embedded: {
        elements: [
          { id: 1, version: 1, comment: { raw: 'Created' } },
          { id: 2, version: 6, comment: { raw: 'Approved' } },
        ],
      },
    },
  });

  const snap = await observer.snapshotObservedFacts();
  observer.detach();
  assert.equal(snap.observed.status, 'observed');
  assert.deepEqual({ ...snap.observed.facts }, {
    'record:/lockVersion': 5,
    'record:/estimatedTime': 'PT24H',
    'record:/statusCode': 2,
    'approval:/lockVersion': 2,
    'approval:/estimatedTime': 'PT24H',
    'approval:/statusCode': 2,
    'revisions:/entryCount': 2,
    'revisions:/latestVersion': 6,
  });
});

test('REJECTS a changed write even when the learned guard passes, and scores all 5 arms cleanly', () => {
  const teachingBinding = computeOpenProjectOperationBinding({
    workPackageId: '10',
    preCommitLockVersion: 2,
    expectedActorHref: '/api/v3/users/101',
    intendedChanges: { statusHref: '/api/v3/statuses/2', estimatedTime: 'PT8H' },
    clientOperationId: 'teach-op-10',
  });

  const frozen = freezeQualificationRepairBundle({
    preUpgradeSteps,
    preUpgradeAuthorityScope: 'org/openproject-local',
    proposedRepair: validSingleStepRepair,
    effectContract: approvedEffectContract,
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

  const guardPassingResponses = [
    resp('record', { id: 21, lockVersion: 5, estimatedTime: 'PT24H' }),
    resp('approval', { id: 3, lockVersion: 2, estimatedTime: 'PT24H' }),
  ];

  // (A) Exact approved mutation on guard-passing route -> `eligible-for-review`:
  const validOut = evaluateHeldOutRouteWithFrozenBundle(frozen, {
    recordId: '21',
    actorHref: '/api/v3/users/101',
    preCommitLockVersion: 5,
    clientOperationId: 'holdout-op-21',
    requestedMutation: {
      method: 'PATCH',
      path: '/api/v3/work_packages/21',
      intendedChanges: { statusHref: '/api/v3/statuses/2', estimatedTime: 'PT24H' },
    },
    responses: guardPassingResponses,
  });
  assert.equal(validOut.status, 'eligible-for-review');
  assert.equal(validOut.rejectedByEffectContract, false);

  // (B) Learned guard STILL passes (`PT24H === PT24H`), BUT requested write changes `statusHref` -> REJECTED!
  const changedFixedStatus = evaluateHeldOutRouteWithFrozenBundle(frozen, {
    recordId: '21',
    actorHref: '/api/v3/users/101',
    preCommitLockVersion: 5,
    clientOperationId: 'holdout-op-21b',
    requestedMutation: {
      method: 'PATCH',
      path: '/api/v3/work_packages/21',
      intendedChanges: { statusHref: '/api/v3/statuses/9', estimatedTime: 'PT24H' },
    },
    responses: guardPassingResponses,
  });
  assert.equal(changedFixedStatus.status, 'abstain');
  assert.equal(changedFixedStatus.rejectedByEffectContract, true);
  assert.equal(changedFixedStatus.reason, 'changed-write-violates-approved-contract');

  // (C) Learned guard STILL passes (`PT24H === PT24H`), BUT requested write alters `estimatedTime` -> REJECTED!
  const changedTermsWrite = evaluateHeldOutRouteWithFrozenBundle(frozen, {
    recordId: '21',
    actorHref: '/api/v3/users/101',
    preCommitLockVersion: 5,
    clientOperationId: 'holdout-op-21c',
    requestedMutation: {
      method: 'PATCH',
      path: '/api/v3/work_packages/21',
      intendedChanges: { statusHref: '/api/v3/statuses/2', estimatedTime: 'PT99H' },
    },
    responses: guardPassingResponses,
  });
  assert.equal(changedTermsWrite.status, 'abstain');
  assert.equal(changedTermsWrite.rejectedByEffectContract, true);
  assert.equal(changedTermsWrite.reason, 'changed-write-diverges-from-approved-terms');

  // (D) Learned guard STILL passes, BUT requested write smuggles an extra unapproved field (`subject`) -> REJECTED!
  const smuggledFieldWrite = evaluateHeldOutRouteWithFrozenBundle(frozen, {
    recordId: '21',
    actorHref: '/api/v3/users/101',
    preCommitLockVersion: 5,
    clientOperationId: 'holdout-op-21d',
    requestedMutation: {
      method: 'PATCH',
      path: '/api/v3/work_packages/21',
      intendedChanges: {
        statusHref: '/api/v3/statuses/2',
        estimatedTime: 'PT24H',
        subject: 'Unapproved Subject Edit',
      },
    },
    responses: guardPassingResponses,
  });
  assert.equal(smuggledFieldWrite.status, 'abstain');
  assert.equal(smuggledFieldWrite.rejectedByEffectContract, true);
  assert.equal(smuggledFieldWrite.reason, 'unapproved-mutation-field');

  // (E) Learned guard STILL passes, BUT requested write targets a different record path -> REJECTED!
  const wrongTargetPath = evaluateHeldOutRouteWithFrozenBundle(frozen, {
    recordId: '21',
    actorHref: '/api/v3/users/101',
    preCommitLockVersion: 5,
    clientOperationId: 'holdout-op-21e',
    requestedMutation: {
      method: 'PATCH',
      path: '/api/v3/work_packages/999',
      intendedChanges: { statusHref: '/api/v3/statuses/2', estimatedTime: 'PT24H' },
    },
    responses: guardPassingResponses,
  });
  assert.equal(wrongTargetPath.status, 'abstain');
  assert.equal(wrongTargetPath.rejectedByEffectContract, true);
  assert.equal(wrongTargetPath.reason, 'unapproved-mutation-endpoint-or-method');

  // (F) 5-arm comparison under matched commit & contract protections:
  const heldOutRoutes = [
    {
      recordId: '21',
      actorHref: '/api/v3/users/101',
      preCommitLockVersion: 5,
      clientOperationId: 'holdout-op-21',
      requestedMutation: {
        method: 'PATCH',
        path: '/api/v3/work_packages/21',
        intendedChanges: { statusHref: '/api/v3/statuses/2', estimatedTime: 'PT24H' },
      },
      groundTruthValidTransfer: true,
      serverRejectsAtCommit: false,
      responses: guardPassingResponses,
    },
    {
      recordId: '22',
      actorHref: '/api/v3/users/101',
      preCommitLockVersion: 3,
      clientOperationId: 'holdout-op-22',
      requestedMutation: {
        method: 'PATCH',
        path: '/api/v3/work_packages/22',
        intendedChanges: { statusHref: '/api/v3/statuses/2', estimatedTime: 'PT8H' },
      },
      groundTruthValidTransfer: false,
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
  assert.equal(byArm['learned-selective-reuse'].verifiedValidTransfers, 1);
  assert.equal(byArm['learned-selective-reuse'].committedWrongEffects, 0);
  assert.equal(byArm['learned-selective-reuse'].planningCalls, 0);
});
