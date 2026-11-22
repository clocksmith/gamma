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
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}
