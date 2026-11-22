import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtempSync, realpathSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { InvestigationStore } from '../../src/client/investigation.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { runWorkflow } from '../../src/client/workflow-agent.js';
import {
  enforcePaidModelGate,
  evaluateReleaseNPlus1,
  evaluateThreeWayPaperRule,
  evaluateUnseenRoutesFromFrozenRepair,
  freezeReleaseNArtifacts,
  hanleyZeroNumeratorUpperBound95,
  repairSharedStepOnceAndFreeze,
  resolveWorkflowArms,
} from '../../qualification/workflow-generalization/release-drift-runner.mjs';
import {
  OPENPROJECT_SERVER_CODE_AUDIT,
  probeErpNextAfterOpenProjectQualifies,
  probeOpenProjectDualRelease,
} from '../../qualification/workflow-generalization/stage2-upstream-contract-probe.mjs';

const LIMITS = Object.freeze({ maxNodes: 96, maxEdges: 128, maxSteps: 32 });
const CONFIG = Object.freeze({ maxTurns: 16, maxInputBytes: 60000 });

// 1. `resolveWorkflowArms` automatically includes `direct-write-api` wherever `evaluateReplayApplicability`
//    says the Direct API suffices (`worthBuildingReplay: false`):
{
  const apiSuffices = resolveWorkflowArms({
    id: 'crud-task',
    hasDirectWriteApi: true,
    requiresPreSubmitUiReview: false,
    requiresInBrowserContextGathering: false,
    explicitBusinessPrerequisites: ['role-active'],
  });
  assert.equal(apiSuffices.applicability.worthBuildingReplay, false);
  assert.equal(apiSuffices.arms[0], 'direct-write-api');

  const uiNeeded = resolveWorkflowArms({
    id: 'pre-submit-review',
    hasDirectWriteApi: false,
    requiresPreSubmitUiReview: true,
    explicitBusinessPrerequisites: ['approval-active'],
  });
  assert.equal(uiNeeded.applicability.worthBuildingReplay, true);
  assert.equal(uiNeeded.arms.includes('direct-write-api'), false);
  assert.equal(uiNeeded.arms.includes('attested-modular-skill'), true);
}

// 2. Mutation-time `assertPrerequisite -> { status: 'unavailable' }` blocks writes under strict mode:
{
  const tmp = mkdtempSync(join(realpathSync(tmpdir()), 's2-unavail-mut-'));
  const store = new InvestigationStore(tmp);
  try {
    let strictWrites = 0;
    const makeSvc = onWrite => ({
      async observe() {
        return {
          url: 'https://unit.invalid/stage',
          text: 'stage',
          observationVersion: 1,
          isTruncated: false,
          elements: [
            {
              role: 'textbox',
              label: 'Note',
              tag: 'input',
              inputType: 'text',
              handle: 'h-n',
              selector: '#h-n',
              digest: 'd1',
              value: '',
              text: '',
              actionability: { visible: true, inert: false, disabled: false },
              formKey: 'f1',
              isDefaultValue: true,
            },
          ],
        };
      },
      outstanding: async () => [],
      async submitAction() {
        onWrite();
        return { result: Promise.resolve({ outcome: 'completed' }) };
      },
    });

    store.create({ id: 'strict-u', goal: 'Test unavailable mutation block' });
    const strictRes = await runWorkflow({
      dag: new TraceDag(LIMITS),
      mode: 'fresh',
      service: makeSvc(() => {
        strictWrites += 1;
      }),
      owner: {},
      pageId: 'main',
      intent: 'u:test',
      template: 'u:v1',
      goal: 'Test unavailable mutation block',
      accountScope: 'org/u',
      recordId: 'R-1',
      inputs: { note: 'hello' },
      intermediateClicks: [],
      observationLocators: null,
      includeFormState: true,
      requireVerifiedEntryPrerequisites: true,
      assertPrerequisite: async () => ({
        status: 'unavailable',
        predicate: 'approval-service',
        reason: 'timeout',
      }),
      planner: {
        identity: { model: 'stub' },
        async next() {
          return { tool: 'act', input: { kind: 'fill', handle: 'h-n', slot: 'note' } };
        },
      },
      task: 'Test unavailable mutation block',
      config: CONFIG,
      store,
      projectId: 'strict-u',
      verifyReview: async () => ({ completed: false }),
      signal: new AbortController().signal,
    });
    assert.equal(strictRes.completed, false);
    assert.equal(strictWrites, 0);
    assert.equal(strictRes.unavailablePredicates?.length, 1);
  } finally {
    store.close();
    rmSync(tmp, { recursive: true, force: true });
  }
}

// 3. Step 5 three-way paper decision rule (`evaluateThreeWayPaperRule`):
{
  assert.throws(
    () => enforcePaidModelGate({ paidModelRequested: true, approvePaidModel: false, maxTotalUsd: 40, maxRunUsd: 2 }),
    err => err.code === 'paid-model-not-authorized',
  );

  const twoAppTieOnGraphButModularWinsLocality = [
    // App 1: OpenProject
    { appId: 'openproject', releasePair: 'v13.4.0->v14.0.0', arm: 'attested-checkpointed-skill', correctCompletions: 3, unseenSiblingPlannerTurns: 8, unseenSiblingCostUsd: 0.32, backendPredicateReads: 8, appLogForbiddenCommits: 0, appLogDuplicateCommits: 0, unverifiedUnavailableWrites: 0, changedRuleCases: 1, changedRuleCleanStops: 1 },
    { appId: 'openproject', releasePair: 'v13.4.0->v14.0.0', arm: 'attested-modular-skill', correctCompletions: 3, unseenSiblingPlannerTurns: 0, unseenSiblingCostUsd: 0.0, backendPredicateReads: 5, appLogForbiddenCommits: 0, appLogDuplicateCommits: 0, unverifiedUnavailableWrites: 0, changedRuleCases: 1, changedRuleCleanStops: 1 },
    { appId: 'openproject', releasePair: 'v13.4.0->v14.0.0', arm: 'gammatron-graph', correctCompletions: 3, unseenSiblingPlannerTurns: 1, unseenSiblingCostUsd: 0.04, backendPredicateReads: 10, appLogForbiddenCommits: 0, appLogDuplicateCommits: 0, unverifiedUnavailableWrites: 0, changedRuleCases: 1, changedRuleCleanStops: 1 },
    // App 2: ERPNext
    { appId: 'erpnext', releasePair: 'v15.10.0->v15.20.0', arm: 'attested-checkpointed-skill', correctCompletions: 3, unseenSiblingPlannerTurns: 9, unseenSiblingCostUsd: 0.36, backendPredicateReads: 9, appLogForbiddenCommits: 0, appLogDuplicateCommits: 0, unverifiedUnavailableWrites: 0, changedRuleCases: 1, changedRuleCleanStops: 1 },
    { appId: 'erpnext', releasePair: 'v15.10.0->v15.20.0', arm: 'attested-modular-skill', correctCompletions: 3, unseenSiblingPlannerTurns: 0, unseenSiblingCostUsd: 0.0, backendPredicateReads: 6, appLogForbiddenCommits: 0, appLogDuplicateCommits: 0, unverifiedUnavailableWrites: 0, changedRuleCases: 1, changedRuleCleanStops: 1 },
    { appId: 'erpnext', releasePair: 'v15.10.0->v15.20.0', arm: 'gammatron-graph', correctCompletions: 3, unseenSiblingPlannerTurns: 1, unseenSiblingCostUsd: 0.04, backendPredicateReads: 12, appLogForbiddenCommits: 0, appLogDuplicateCommits: 0, unverifiedUnavailableWrites: 0, changedRuleCases: 1, changedRuleCleanStops: 1 },
  ];

  const verdictA = evaluateThreeWayPaperRule({
    clusters: twoAppTieOnGraphButModularWinsLocality,
    isPaidLiveRun: true,
  });
  assert.equal(verdictA.outcome, 'outcome-a-drop-graph-claim-ship-modular-repair-locality');

  // If an app-log forbidden commit occurs, Outcome C (negative/null) triggers immediately:
  const brokenSafety = structuredClone(twoAppTieOnGraphButModularWinsLocality);
  brokenSafety[1].appLogForbiddenCommits = 1;
  const verdictC = evaluateThreeWayPaperRule({ clusters: brokenSafety, isPaidLiveRun: true });
  assert.equal(verdictC.outcome, 'outcome-c-negative-or-null-transfer');
}

// 4. `evaluateReleaseNPlus1` application-log oracle + `changed-rule-same-screen` + `direct-write-api` arm:
{
  const tmp = mkdtempSync(join(realpathSync(tmpdir()), 's2-runner-check-'));
  try {
    const mkHost = ({ rel, branch, ruleHolds = true }) => {
      let screen = branch === 'mid' ? 'stage' : 'intake';
      let obsVer = 0;
      let inVal = '';
      let title = '';
      let tag = '';
      let appCommits = 0;
      let appForbidden = 0;
      const mk = (role, label, t, it, h, v = '') => ({
        role, label, tag: t, inputType: it, handle: h, selector: `#${h}`,
        digest: `${rel}-${h}-${v}`, value: v, text: t === 'button' ? label : '',
        actionability: { visible: true, inert: false, disabled: false },
        formKey: t === 'input' ? `f-${screen}` : null, isDefaultValue: v === '',
      });
      return {
        expected: { complete: ruleHolds },
        readApplicationLogEffects: async () => ({
          commits: appCommits,
          forbiddenCommits: appForbidden,
          duplicateCommits: 0,
          backendReads: 1,
        }),
        attestPrerequisites: async ({ skipped }) =>
          skipped.map(() => ({
            holds: ruleHolds,
            account: 'org/a',
            record: 'R-1',
            predicate: 'rule-v2',
            version: 1,
          })),
        assertPrerequisite: async () => (ruleHolds ? { ok: true } : { ok: false, reason: 'changed-rule-denied' }),
        service: {
          async observe() {
            const urlPath = screen === 'intake' ? `in-${branch}` : screen;
            const elements = screen === 'intake'
              ? [mk('textbox', branch === 'a1' ? 'Ref A1' : 'Ref A2', 'input', 'text', 'h-in', inVal), mk('button', 'To Stage', 'button', '', 'h-b1')]
              : screen === 'stage'
                ? [
                    ...(rel === 'v2' ? [mk('textbox', 'Upgrade Field', 'input', 'text', 'h-up', tag)] : []),
                    mk('textbox', 'Title', 'input', 'text', 'h-t', title),
                    mk('button', 'Review', 'button', '', 'h-b2'),
                  ]
                : [mk('status', 'Done', 'output', '', 'h-done')];
            return { url: `https://u.invalid/${urlPath}`, text: screen, observationVersion: ++obsVer, isTruncated: false, elements };
          },
          outstanding: async () => [],
          async submitAction(cmd) {
            if (cmd.kind === 'click') {
              if (screen === 'stage') {
                appCommits += 1;
                if (!ruleHolds) appForbidden += 1;
              }
              screen = screen === 'intake' ? 'stage' : 'done';
            } else if (cmd.target.handle === 'h-in') inVal = cmd.params.value;
            else if (cmd.target.handle === 'h-t') title = cmd.params.value;
            else if (cmd.target.handle === 'h-up') tag = cmd.params.value;
            return { result: Promise.resolve({ outcome: 'completed' }) };
          },
        },
        planner: {
          identity: { model: 'stub' },
          async next({ observation }) {
            for (const [l, s] of [['Ref A1', 'a1'], ['Ref A2', 'a2'], ['Upgrade Field', 'up'], ['Title', 'title']]) {
              const e = observation.elements.find(x => x.label === l);
              if (e && !e.value) return { tool: 'act', input: { kind: 'fill', handle: e.handle, slot: s } };
            }
            const b = observation.elements.find(x => x.role === 'button');
            if (b) return { tool: 'act', input: { kind: 'click', handle: b.handle } };
            return { tool: 'finish', input: { summary: 'done' } };
          },
        },
        verifyReview: async () => ({ completed: ruleHolds && screen === 'done' && title === 'T' && (rel === 'v1' || tag === 'U') }),
      };
    };

    const wf = {
      id: 'unit-sibling-locality',
      hasDirectWriteApi: true,
      requiresPreSubmitUiReview: false,
      explicitBusinessPrerequisites: ['rule-v2'],
      executeDirectApi: async tc => ({
        expectedComplete: tc.caseKind !== 'changed-rule-same-screen',
        completed: tc.caseKind !== 'changed-rule-same-screen',
        backendPredicateReads: 1,
        appLogCommits: tc.caseKind === 'changed-rule-same-screen' ? 0 : 1,
        appLogForbiddenCommits: 0,
        appLogDuplicateCommits: 0,
      }),
      intent: 'u:s',
      template: 'u:s:v1',
      goal: 'Sibling repair locality check',
      accountScope: 'org/a',
      intermediateClicks: [['button', 'To Stage', 'button', ''], ['button', 'Review', 'button', '']],
      teachReleaseN: () => [
        { id: 't1', inputs: { a1: '1', title: 'T' }, build: () => mkHost({ rel: 'v1', branch: 'a1' }) },
        { id: 't2', inputs: { a2: '2', title: 'T' }, build: () => mkHost({ rel: 'v1', branch: 'a2' }) },
      ],
      casesReleaseNPlus1: () => [
        { id: 'c1-repair', cohortId: 'k', learnRepairs: true, inputs: { a1: '1', up: 'U', title: 'T' }, build: () => mkHost({ rel: 'v2', branch: 'a1' }) },
        { id: 'c2-unseen-sibling', cohortId: 'k', learnRepairs: true, isUnseenSiblingRoute: true, inputs: { a2: '2', up: 'U', title: 'T' }, build: () => mkHost({ rel: 'v2', branch: 'a2' }) },
        { id: 'mnp-changed-rule', cohortId: 'k', caseKind: 'changed-rule-same-screen', inputs: { up: 'U', title: 'T' }, build: () => mkHost({ rel: 'v2', branch: 'mid', ruleHolds: false }) },
      ],
    };

    await freezeReleaseNArtifacts({ appId: 'u', releaseN: 'v1', workflowSpec: wf, outDir: tmp });
    const out = await evaluateReleaseNPlus1({ releaseN1: 'v2', workflowSpec: wf, manifestDir: tmp });
    assert.ok(out.clusters.some(c => c.arm === 'direct-write-api'));
    const mod = out.clusters.find(c => c.arm === 'attested-modular-skill');
    const graph = out.clusters.find(c => c.arm === 'gammatron-graph');
    assert.equal(mod.unseenSiblingPlannerTurns, 0, 'Modular skill serves untouched sibling route in 0 turns');
    assert.equal(graph.unseenSiblingPlannerTurns, 1, 'Graph takes 1 turn on untouched sibling caller before reconvergence');
    assert.equal(mod.changedRuleCleanStops, 1);
    assert.equal(mod.appLogForbiddenCommits, 0);

    // 5. Explicit Phase B (`repairSharedStepOnceAndFreeze`) -> Phase C (`evaluateUnseenRoutesFromFrozenRepair` with `learnRepairs: false`):
    const phaseBDir = join(tmp, 'phase-b');
    const phaseB = await repairSharedStepOnceAndFreeze({
      releaseN1: 'v2',
      workflowSpec: wf,
      manifestDir: tmp,
      repairRouteSpec: { id: 'c1-repair', inputs: { a1: '1', up: 'U', title: 'T' }, build: () => mkHost({ rel: 'v2', branch: 'a1' }) },
      outDir: phaseBDir,
    });
    assert.equal(phaseB.repairedOnRouteId, 'c1-repair');

    const phaseC = await evaluateUnseenRoutesFromFrozenRepair({
      workflowSpec: wf,
      repairManifestDir: phaseBDir,
      unseenCases: [
        { id: 'c2-unseen-sibling', isUnseenSiblingRoute: true, inputs: { a2: '2', up: 'U', title: 'T' }, build: () => mkHost({ rel: 'v2', branch: 'a2' }) },
        { id: 'mnp-changed-rule', caseKind: 'changed-rule-same-screen', inputs: { up: 'U', title: 'T' }, build: () => mkHost({ rel: 'v2', branch: 'mid', ruleHolds: false }) },
      ],
    });
    const modPhaseC = phaseC.clusters.find(c => c.arm === 'attested-modular-skill');
    assert.equal(modPhaseC.verifiedCompletions, 1);
    assert.equal(modPhaseC.correctRefusals, 1);
    assert.equal(modPhaseC.unseenRoutesRestoredZeroTurns, 1);
    assert.equal(modPhaseC.wrongRepairsSpreadCount, 0);
    assert.equal(modPhaseC.provokedForbiddenTrials, 1);
    assert.equal(modPhaseC.unseenSiblingPlannerTurns, 0);
    assert.equal(hanleyZeroNumeratorUpperBound95(100), 0.029513);
    assert.deepEqual(phaseC.paperDecision.metricHierarchy, [
      'verifiedCompletions',
      'correctRefusals',
      'plannerTurns',
      'backendPredicateReads',
      'costUsd',
    ]);
    assert.equal(phaseC.paperDecision.shippedDefaultRepresentation, 'attested-modular-skill');
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

// 6. Dual-release OpenProject 13.4.0 -> 14.0.0 qualification probe + specific-terms ABA + lost-ack reconciliation + ERPNext gate:
{
  assert.equal(OPENPROJECT_SERVER_CODE_AUDIT.v13_4_0_commit, 'f8d6a196a180155d69998d73f796fa1f177b16bb');
  assert.equal(OPENPROJECT_SERVER_CODE_AUDIT.v14_0_0_commit, 'aa7a72a913cb619b3f976ff5f411ef7af97b6caa');

  // ERPNext is deferred until OpenProject qualifies on both releases:
  const deferredErp = await probeErpNextAfterOpenProjectQualifies({}, { dualReleaseQualified: false });
  assert.equal(deferredErp.status, 'deferred-until-openproject-13.4-to-14.0-workflow-qualifies');

  // Faithful in-memory OpenProject API v3 simulator modeling `OpenProject::Mutex.with_advisory_lock_transaction` + `lock_version` + `journals`:
  const startMockOpenProject = async () => {
    let nextId = 1;
    const wps = new Map();
    const mutexChains = new Map();
    const withWpMutex = (id, fn) => {
      const prev = mutexChains.get(id) ?? Promise.resolve();
      const next = prev.then(fn, fn);
      mutexChains.set(id, next);
      return next;
    };

    const srv = createServer((req, res) => {
      const chunks = [];
      req.on('data', c => chunks.push(c));
      req.on('end', async () => {
        const raw = Buffer.concat(chunks).toString('utf8');
        const body = raw ? JSON.parse(raw) : {};
        const url = new URL(req.url, 'http://127.0.0.1');
        const send = (status, obj) => {
          res.writeHead(status, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify(obj));
        };

        if (req.method === 'POST' && /^\/api\/v3\/projects\/[^/]+\/work_packages$/.test(url.pathname)) {
          const id = nextId++;
          const wp = {
            id,
            lockVersion: 0,
            subject: body.subject ?? '',
            estimatedTime: body.estimatedTime ?? null,
            description: body.description ?? { raw: '' },
            statusHref: '/api/v3/statuses/1',
            parentHref: body._links?.parent?.href ?? null,
            journals: [{ id: 1, version: 1, comment: { raw: 'Created' } }],
          };
          wps.set(id, wp);
          return send(201, {
            id: wp.id,
            lockVersion: wp.lockVersion,
            subject: wp.subject,
            estimatedTime: wp.estimatedTime,
            description: wp.description,
            _links: { status: { href: wp.statusHref } },
          });
        }

        const actMatch = url.pathname.match(/^\/api\/v3\/work_packages\/(\d+)\/activities$/);
        if (req.method === 'GET' && actMatch) {
          const wp = wps.get(Number(actMatch[1]));
          if (!wp) return send(404, { message: 'not found' });
          return send(200, { _embedded: { elements: wp.journals } });
        }

        const wpMatch = url.pathname.match(/^\/api\/v3\/work_packages\/(\d+)$/);
        if (wpMatch && req.method === 'GET') {
          const wp = wps.get(Number(wpMatch[1]));
          if (!wp) return send(404, { message: 'not found' });
          return send(200, {
            id: wp.id,
            lockVersion: wp.lockVersion,
            subject: wp.subject,
            estimatedTime: wp.estimatedTime,
            description: wp.description,
            _links: { status: { href: wp.statusHref } },
          });
        }

        if (wpMatch && req.method === 'PATCH') {
          const id = Number(wpMatch[1]);
          return withWpMutex(id, async () => {
            await new Promise(r => setTimeout(r, 8));
            const wp = wps.get(id);
            if (!wp) return send(404, { message: 'not found' });
            if (body.lockVersion !== wp.lockVersion) {
              return send(409, { errorIdentifier: 'urn:openproject-org:api:v3:errors:UpdateConflict' });
            }
            if (body._links?.status?.href === '/api/v3/statuses/99') {
              return send(422, { errorIdentifier: 'urn:openproject-org:api:v3:errors:PropertyConstraintViolation' });
            }
            wp.lockVersion += 1;
            if (body.estimatedTime !== undefined) wp.estimatedTime = body.estimatedTime;
            if (body.description !== undefined) wp.description = body.description;
            if (body._links?.status?.href) wp.statusHref = body._links.status.href;
            wp.journals.push({
              id: wp.journals.length + 1,
              version: wp.lockVersion + 1,
              comment: { raw: body.journalNotes ?? '' },
            });
            return send(200, {
              id: wp.id,
              lockVersion: wp.lockVersion,
              subject: wp.subject,
              estimatedTime: wp.estimatedTime,
              description: wp.description,
              _links: { status: { href: wp.statusHref } },
            });
          });
        }
        return send(404, {});
      });
    });

    await new Promise(r => srv.listen(0, '127.0.0.1', r));
    const port = srv.address().port;
    return { url: `http://127.0.0.1:${port}`, close: () => new Promise(r => srv.close(r)) };
  };

  const op13 = await startMockOpenProject();
  const op14 = await startMockOpenProject();
  try {
    const dual = await probeOpenProjectDualRelease(
      {
        openprojectV13Url: op13.url,
        openprojectV14Url: op14.url,
        openprojectProjectId: 'demo-proj',
        openprojectAuthorToken: 'author-tok',
        openprojectApproverToken: 'approver-tok',
        openprojectApprovedStatusHref: '/api/v3/statuses/2',
        openprojectHoldStatusHref: '/api/v3/statuses/3',
        openprojectDisallowedStatusHref: '/api/v3/statuses/99',
      },
      { dockerAvailable: false, detail: 'unit-loopback' },
    );
    assert.equal(dual.status, 'probed-both-releases');
    assert.equal(dual.dualReleaseQualified, true, JSON.stringify(dual.v13_4_0?.checks, null, 2));
    assert.equal(dual.v13_4_0.checks.sameRowSpecificTermsAbaRefused.passes, true);
    assert.equal(dual.v13_4_0.checks.separateEntityAbaDiagnostic.separateEntityAbaRequiresExplicitVersionValidator, true);
    assert.equal(dual.v14_0_0.checks.concurrentSameRowRaceSerialized.passes, true);
    assert.equal(dual.v14_0_0.checks.lostAckReconciliation.passes, true);

    const readyErp = await probeErpNextAfterOpenProjectQualifies({}, dual);
    assert.equal(readyErp.status, 'awaiting-owner-approved-erpnext-containers-and-accounts');
  } finally {
    await op13.close();
    await op14.close();
  }
}
