#!/usr/bin/env node
// Stage 2 Real-Application Upgrade Runner (`Release N -> Release N+1`, #88 Steps 3–5):
//
// Enforces the pre-registered Stage 2 protocol (`stage2-real-upgrade-preregistration.md`):
//   1. `direct-write-api` arm included automatically wherever `evaluateReplayApplicability`
//      reports `worthBuildingReplay: false` (API suffices without pre-submit UI review).
//   2. Equal equipment across `attested-checkpointed-skill`, `attested-modular-skill`, and
//      `gammatron-graph`: identical model, prompt, scoped observations (`includeFormState: true`),
//      backend `attestPrerequisites` / `assertPrerequisite`, authorization, journal, and budget,
//      starting from one SHA-256-pinned `Release N` teaching pass (`pairTeaching: true`).
//   3. Post-upgrade repair locality (`cohortId` + `learnRepairs: true`): repair once on the
//      primary route, then evaluate untouched sibling routes held by a separate session.
//   4. Application-log effect oracle (`readApplicationLogEffects`): counts commits, forbidden
//      commits, and duplicate commits directly from the target application's own logs/DB,
//      reporting `(plannerTurns, costUsd, backendPredicateReads)` side-by-side per route, plus
//      same-screen `changed-rule` negative pairs (`mustStopOnChangedRule`).
//   5. Paid model calls remain strictly blocked unless `--approve-paid-model` is passed with
//      owner-approved `--max-total-usd` and `--max-run-usd` ceilings ($0 spent to date).

import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  AttestedSkillBook,
  createAttestedSkillPlanner,
  recordAttestedSkillTeaching,
} from '../../src/client/attested-skill.js';
import { createCliPlanner } from '../../src/client/cli-planner.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { createPlanner } from '../../src/client/planner.js';
import { SuffixIndex } from '../../src/client/suffix-eligibility.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import {
  evaluateReplayApplicability,
  runWorkflow,
  WORKFLOW_SYSTEM,
  WORKFLOW_TOOLS,
} from '../../src/client/workflow-agent.js';

const LIMITS = Object.freeze({ maxNodes: 128, maxEdges: 160, maxSteps: 36 });
const CONFIG = Object.freeze({ maxTurns: 24, maxInputBytes: 60000 });
const sha256 = text => createHash('sha256').update(text, 'utf8').digest('hex');

export const STAGE2_UI_ARMS = Object.freeze([
  'fresh',
  'attested-linear-skill',
  'attested-checkpointed-skill',
  'attested-modular-skill',
  'gammatron-graph',
]);

export const PREREGISTERED_THRESHOLDS = Object.freeze({
  tieMarginCalls: 2,
  tieMarginCostPct: 15,
  repairLocalityMinSavedCalls: 4,
  repairLocalityMinSavedCostPct: 20,
  leanerReadsTieBreakerPct: 25,
  requiredAuditedAppsCount: 2,
});

export function enforcePaidModelGate({
  paidModelRequested = false,
  approvePaidModel = false,
  maxTotalUsd = null,
  maxRunUsd = null,
} = {}) {
  if (!paidModelRequested) return { mode: 'local-zero-dollar', maxTotalUsd: 0, maxRunUsd: 0 };
  if (approvePaidModel !== true) {
    throw Object.assign(
      Error(
        'Paid model calls are blocked: pass --approve-paid-model with owner-approved --max-total-usd and --max-run-usd ($40 total / $2 per run are proposals only).',
      ),
      { code: 'paid-model-not-authorized' },
    );
  }
  if (!(Number(maxTotalUsd) > 0) || !(Number(maxRunUsd) > 0) || Number(maxRunUsd) > Number(maxTotalUsd)) {
    throw Object.assign(Error('Explicit positive --max-total-usd and --max-run-usd ceilings required'), {
      code: 'invalid-spend-ceiling',
    });
  }
  return { mode: 'authorized-paid-model', maxTotalUsd: Number(maxTotalUsd), maxRunUsd: Number(maxRunUsd) };
}

/** Determine active arms for a workflow, adding `direct-write-api` whenever the API suffices. */
export function resolveWorkflowArms(workflowSpec, requestedUiArms = STAGE2_UI_ARMS) {
  const applicability = evaluateReplayApplicability({
    hasDirectWriteApi: Boolean(workflowSpec?.hasDirectWriteApi),
    requiresPreSubmitUiReview: Boolean(workflowSpec?.requiresPreSubmitUiReview),
    requiresInBrowserContextGathering: Boolean(workflowSpec?.requiresInBrowserContextGathering),
    explicitBusinessPrerequisites: workflowSpec?.explicitBusinessPrerequisites ?? ['domain-prerequisite'],
  });
  const includeDirectApi = !applicability.worthBuildingReplay || typeof workflowSpec?.executeDirectApi === 'function';
  return {
    applicability,
    arms: includeDirectApi ? ['direct-write-api', ...requestedUiArms] : [...requestedUiArms],
  };
}

export function createAuthorizedLivePlanner({
  gate,
  provider = 'claude-cli',
  model = 'sonnet',
  directory,
  endpoint = null,
  apiKey = null,
  executable = process.env.FAWN_CLAUDE_BIN ?? 'claude',
  spendTracker,
}) {
  const checked = enforcePaidModelGate({
    paidModelRequested: true,
    approvePaidModel: gate?.approvePaidModel === true,
    maxTotalUsd: gate?.maxTotalUsd,
    maxRunUsd: gate?.maxRunUsd,
  });
  const basePlanner = provider === 'http-api'
    ? createPlanner({ model, endpoint, apiKey, maxOutputTokens: 1024, timeoutMs: 60000 })
    : createCliPlanner({
        executable,
        model,
        directory,
        config: {
          cliMaxBudgetUsd: checked.maxRunUsd,
          cliTerminationGraceMs: 2000,
          modelTimeoutMs: 60000,
          maxBodyBytes: 262144,
        },
        system: WORKFLOW_SYSTEM,
        tools: WORKFLOW_TOOLS,
      });
  if (!basePlanner) throw Error('Live planner configuration is incomplete');
  return {
    identity: { ...basePlanner.identity, liveLlm: true },
    async next(context, opts) {
      if ((spendTracker.spentUsd ?? 0) + checked.maxRunUsd > checked.maxTotalUsd) {
        throw Object.assign(Error('Stage 2 total spend ceiling reached'), { code: 'spend-ceiling-reached' });
      }
      const { rawObservation: _r, unfilteredElements: _u, intermediateClickLocators: _i, ...compact } = context;
      const decision = await basePlanner.next(compact, opts);
      const turnCost = Number.isFinite(decision?.usage?.costUsd) ? decision.usage.costUsd : 0;
      spendTracker.spentUsd = Number(((spendTracker.spentUsd ?? 0) + turnCost).toFixed(6));
      spendTracker.liveCalls = (spendTracker.liveCalls ?? 0) + 1;
      return decision;
    },
  };
}

/** Cluster-level summary grouped by `(appId, releasePair, workflowId, arm)` with application-log counts. */
export function summarizeByWorkflowReleaseCluster(rows) {
  const clusters = new Map();
  for (const row of rows) {
    const key = `${row.appId}|${row.releasePair}|${row.workflowId}|${row.arm}`;
    if (!clusters.has(key)) {
      clusters.set(key, {
        appId: row.appId,
        releasePair: row.releasePair,
        workflowId: row.workflowId,
        arm: row.arm,
        runs: 0,
        correctCompletions: 0,
        falseRefusals: 0,
        changedRuleCases: 0,
        changedRuleCleanStops: 0,
        unseenSiblingRouteRuns: 0,
        unseenSiblingPlannerTurns: 0,
        unseenSiblingCostUsd: 0,
        unseenSiblingBackendReads: 0,
        plannerTurns: 0,
        backendPredicateReads: 0,
        costUsd: 0,
        totalLatencyMs: 0,
        appLogCommits: 0,
        appLogForbiddenCommits: 0,
        appLogDuplicateCommits: 0,
        unverifiedUnavailableWrites: 0,
        repeatedRepairs: 0,
        humanRecoveriesRequired: 0,
        perRoute: [],
      });
    }
    const c = clusters.get(key);
    c.runs += 1;
    const forb = row.appLogForbiddenCommits ?? row.forbiddenEffects ?? 0;
    const dup = row.appLogDuplicateCommits ?? row.duplicateEffects ?? 0;
    const unv = row.unverifiedUnavailableWrites ?? 0;
    if (row.expectedComplete && row.completed && forb === 0 && dup === 0 && unv === 0) {
      c.correctCompletions += 1;
    }
    if (row.expectedComplete && !row.completed) c.falseRefusals += 1;
    if (row.caseKind === 'changed-rule-same-screen') {
      c.changedRuleCases += 1;
      if (!row.completed && forb === 0 && (row.appLogCommits ?? 0) === 0) {
        c.changedRuleCleanStops += 1;
      }
    }
    if (row.isUnseenSiblingRoute) {
      c.unseenSiblingRouteRuns += 1;
      c.unseenSiblingPlannerTurns += row.plannerTurns;
      c.unseenSiblingCostUsd = Number((c.unseenSiblingCostUsd + (row.costUsd ?? 0)).toFixed(6));
      c.unseenSiblingBackendReads += row.backendPredicateReads ?? row.predicateReads ?? 0;
    }
    c.plannerTurns += row.plannerTurns;
    c.backendPredicateReads += row.backendPredicateReads ?? row.predicateReads ?? 0;
    c.costUsd = Number((c.costUsd + (row.costUsd ?? 0)).toFixed(6));
    c.totalLatencyMs = Number((c.totalLatencyMs + row.latencyMs).toFixed(2));
    c.appLogCommits += row.appLogCommits ?? 0;
    c.appLogForbiddenCommits += forb;
    c.appLogDuplicateCommits += dup;
    c.unverifiedUnavailableWrites += unv;
    if (row.repeatedRepair) c.repeatedRepairs += 1;
    if (row.requiresHumanRecovery) c.humanRecoveriesRequired += 1;
    c.perRoute.push({
      caseId: row.caseId,
      routeId: row.routeId ?? row.caseId,
      caseKind: row.caseKind ?? (row.expectedComplete ? 'completable' : 'must-not-proceed'),
      completed: row.completed,
      plannerTurns: row.plannerTurns,
      costUsd: Number((row.costUsd ?? 0).toFixed(6)),
      backendPredicateReads: row.backendPredicateReads ?? row.predicateReads ?? 0,
      latencyMs: row.latencyMs,
      appLogCommits: row.appLogCommits ?? 0,
      appLogForbiddenCommits: forb,
      appLogDuplicateCommits: dup,
    });
  }
  return [...clusters.values()];
}

/** Step 5 pre-registered three-way paper decision rule across two audited upstream app upgrades. */
export function evaluateThreeWayPaperRule({
  clusters,
  thresholds = PREREGISTERED_THRESHOLDS,
  isPaidLiveRun = false,
} = {}) {
  const appUpgrades = [...new Set(clusters.map(c => `${c.appId}|${c.releasePair}`))];
  const perApp = [];

  for (const appKey of appUpgrades) {
    const group = clusters.filter(c => `${c.appId}|${c.releasePair}` === appKey);
    const byArm = Object.fromEntries(group.map(c => [c.arm, c]));
    const ckpt = byArm['attested-checkpointed-skill'];
    const mod = byArm['attested-modular-skill'];
    const graph = byArm['gammatron-graph'];
    const directApi = byArm['direct-write-api'] ?? null;

    const safetyClean = [ckpt, mod, graph]
      .filter(Boolean)
      .every(
        c =>
          c.appLogForbiddenCommits === 0
          && c.appLogDuplicateCommits === 0
          && c.unverifiedUnavailableWrites === 0
          && c.changedRuleCleanStops === c.changedRuleCases,
      );

    const savedCallsModVsCkpt = ckpt && mod ? ckpt.unseenSiblingPlannerTurns - mod.unseenSiblingPlannerTurns : 0;
    const savedCallsPctModVsCkpt =
      ckpt && mod && ckpt.unseenSiblingPlannerTurns > 0
        ? Number(((savedCallsModVsCkpt / ckpt.unseenSiblingPlannerTurns) * 100).toFixed(2))
        : 0;
    const savedCostPctModVsCkpt =
      ckpt && mod && ckpt.unseenSiblingCostUsd > 0
        ? Number((((ckpt.unseenSiblingCostUsd - mod.unseenSiblingCostUsd) / ckpt.unseenSiblingCostUsd) * 100).toFixed(2))
        : null;

    const repairLocalityPasses = Boolean(
      safetyClean
        && ckpt
        && mod
        && mod.correctCompletions >= ckpt.correctCompletions
        && savedCallsModVsCkpt >= thresholds.repairLocalityMinSavedCalls
        && savedCallsPctModVsCkpt >= thresholds.repairLocalityMinSavedCostPct
        && (savedCostPctModVsCkpt === null || savedCostPctModVsCkpt >= thresholds.repairLocalityMinSavedCostPct),
    );

    const graphCallEdgeOverMod = mod && graph ? mod.unseenSiblingPlannerTurns - graph.unseenSiblingPlannerTurns : 0;
    const graphCostEdgePctOverMod =
      mod && graph && mod.unseenSiblingCostUsd > 0
        ? Number((((mod.unseenSiblingCostUsd - graph.unseenSiblingCostUsd) / mod.unseenSiblingCostUsd) * 100).toFixed(2))
        : 0;
    const graphClearsMarginOverModular = Boolean(
      safetyClean
        && mod
        && graph
        && graph.correctCompletions >= mod.correctCompletions
        && graphCallEdgeOverMod > thresholds.tieMarginCalls
        && (!isPaidLiveRun || graphCostEdgePctOverMod > thresholds.tieMarginCostPct),
    );

    perApp.push({
      appUpgrade: appKey,
      safetyClean,
      directApiSufficed: Boolean(directApi && directApi.correctCompletions >= (mod?.correctCompletions ?? 0)),
      repairLocalityPasses,
      savedCallsModVsCkpt,
      savedCallsPctModVsCkpt,
      savedCostPctModVsCkpt,
      graphClearsMarginOverModular,
      graphCallEdgeOverMod,
      graphCostEdgePctOverMod,
      modularBackendReads: mod?.backendPredicateReads ?? null,
      graphBackendReads: graph?.backendPredicateReads ?? null,
    });
  }

  const replicatedOnTwoApps = appUpgrades.length >= thresholds.requiredAuditedAppsCount;
  const allSafetyClean = perApp.length > 0 && perApp.every(a => a.safetyClean);
  const repairLocalityReplicated = replicatedOnTwoApps && perApp.every(a => a.repairLocalityPasses);
  const graphSuperiorityReplicated = replicatedOnTwoApps && perApp.every(a => a.graphClearsMarginOverModular);

  let outcome = 'pending-two-app-live-replication';
  if (replicatedOnTwoApps && isPaidLiveRun) {
    if (!allSafetyClean || !repairLocalityReplicated) {
      outcome = 'outcome-c-negative-or-null-transfer';
    } else if (graphSuperiorityReplicated) {
      outcome = 'outcome-b-retain-narrow-multi-exit-graph-claim';
    } else {
      outcome = 'outcome-a-drop-graph-claim-ship-modular-repair-locality';
    }
  }

  return {
    isPaidLiveRun,
    auditedAppsEvaluated: appUpgrades.length,
    requiredAuditedApps: thresholds.requiredAuditedAppsCount,
    defaultGraphDispositionOnTie: 'drop-graph-claim',
    outcome,
    perApp,
  };
}

/** Teach ONCE on Release N (`pairTeaching: true`) and SHA-256-pin frozen artifacts. */
export async function freezeReleaseNArtifacts({
  appId,
  releaseN,
  workflowSpec,
  outDir,
  uiArms = STAGE2_UI_ARMS,
  pairTeaching = true,
}) {
  const { applicability } = resolveWorkflowArms(workflowSpec, uiArms);
  mkdirSync(outDir, { recursive: true });
  const storeRoot = mkdtempSync(join(realpathSync(tmpdir()), 'rel-n-teach-'));
  const store = new InvestigationStore(storeRoot);
  let seq = 0;
  const artifacts = {};

  try {
    if (pairTeaching) {
      const sharedDag = new TraceDag(LIMITS);
      const sharedIndex = new SuffixIndex();
      const sharedBook = new AttestedSkillBook();
      let sharedTeachTurns = 0;
      const t0 = performance.now();

      for (const spec of workflowSpec.teachReleaseN()) {
        const host = await spec.build();
        try {
          let runTurns = 0;
          const basePlanner = {
            identity: host.planner.identity,
            next: (...a) => {
              runTurns += 1;
              return host.planner.next(...a);
            },
          };
          const rec = recordAttestedSkillTeaching(basePlanner, {
            book: sharedBook,
            accountScope: workflowSpec.accountScope,
          });
          const pid = `rn-${++seq}`;
          store.create({ id: pid, goal: workflowSpec.goal });
          const res = await runWorkflow({
            dag: sharedDag,
            mode: 'learn',
            service: host.service,
            owner: host.owner ?? {},
            pageId: host.pageId ?? 'main',
            intent: workflowSpec.intent,
            template: workflowSpec.template,
            goal: workflowSpec.goal,
            accountScope: workflowSpec.accountScope,
            recordId: spec.recordId ?? null,
            inputs: spec.inputs,
            intermediateClicks: workflowSpec.intermediateClicks,
            observationLocators: workflowSpec.observationLocators ?? null,
            includeFormState: true,
            learnRepairs: false,
            reconvergeMidRepair: false,
            planner: rec.planner,
            suffixIndex: sharedIndex,
            effectForStep: host.effectForStep ?? null,
            task: workflowSpec.goal,
            config: CONFIG,
            store,
            projectId: pid,
            verifyReview: host.verifyReview,
            signal: new AbortController().signal,
          });
          assert.equal(res.completed, true, `Release N teaching failed: ${res.detail}`);
          sharedTeachTurns += runTurns;
          rec.commitVerified(await host.service.observe({ ...(host.owner ?? {}), includeFormState: true }), spec.inputs);
        } finally {
          if (typeof host.close === 'function') await host.close();
        }
      }

      const teachLatencyMs = Number((performance.now() - t0).toFixed(2));
      for (const arm of uiArms) {
        const isGraph = arm === 'gammatron-graph';
        const isFresh = arm === 'fresh';
        const payload = JSON.stringify(
          {
            appId,
            releaseN,
            workflowId: workflowSpec.id,
            arm,
            pairedSingleTeachingPass: true,
            teachTurns: isFresh ? 0 : sharedTeachTurns,
            teachLatencyMs: isFresh ? 0 : teachLatencyMs,
            graph: isGraph ? sharedDag.export() : null,
            index: isGraph ? sharedIndex.export() : null,
            book: !isGraph && !isFresh ? sharedBook.export() : null,
          },
          null,
          2,
        );
        const fileName = `frozen-${workflowSpec.id}-${arm}.json`;
        writeFileSync(join(outDir, fileName), payload + '\n');
        artifacts[arm] = { file: fileName, sha256: sha256(payload + '\n') };
      }
    }
  } finally {
    store.close();
    rmSync(storeRoot, { recursive: true, force: true });
  }

  const manifest = { appId, releaseN, workflowId: workflowSpec.id, applicability, artifacts };
  writeFileSync(join(outDir, 'release-n-manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  return manifest;
}

/** Evaluate frozen Release N artifacts on Release N+1 routes (including `direct-write-api` arm when applicable). */
export async function evaluateReleaseNPlus1({
  releaseN1,
  workflowSpec,
  manifestDir,
  uiArms = STAGE2_UI_ARMS,
  requireVerifiedEntryPrerequisites = true,
  isPaidLiveRun = false,
}) {
  const { applicability, arms } = resolveWorkflowArms(workflowSpec, uiArms);
  const manifest = JSON.parse(readFileSync(join(manifestDir, 'release-n-manifest.json'), 'utf8'));
  const loaded = {};
  for (const arm of uiArms) {
    const entry = manifest.artifacts[arm];
    const raw = readFileSync(join(manifestDir, entry.file), 'utf8');
    if (sha256(raw) !== entry.sha256) {
      throw Error(`Frozen Release N artifact checksum mismatch for ${arm}`);
    }
    loaded[arm] = JSON.parse(raw);
  }

  const storeRoot = mkdtempSync(join(realpathSync(tmpdir()), 'rel-n1-eval-'));
  const store = new InvestigationStore(storeRoot);
  let seq = 0;
  const rows = [];
  const cohortState = new Map();
  const cohortCounters = new Map();

  try {
    for (const testCase of workflowSpec.casesReleaseNPlus1()) {
      for (const arm of arms) {
        if (arm === 'direct-write-api') {
          if (typeof workflowSpec.executeDirectApi !== 'function') continue;
          const t0 = performance.now();
          const apiRes = await workflowSpec.executeDirectApi(testCase);
          rows.push({
            appId: manifest.appId,
            releasePair: `${manifest.releaseN}->${releaseN1}`,
            workflowId: workflowSpec.id,
            caseId: testCase.id,
            routeId: testCase.routeId ?? testCase.id,
            caseKind: testCase.caseKind ?? (apiRes.expectedComplete ? 'completable' : 'must-not-proceed'),
            isUnseenSiblingRoute: Boolean(testCase.isUnseenSiblingRoute),
            arm: 'direct-write-api',
            expectedComplete: Boolean(apiRes.expectedComplete),
            completed: Boolean(apiRes.completed),
            plannerTurns: 0,
            backendPredicateReads: apiRes.backendPredicateReads ?? 0,
            costUsd: 0,
            latencyMs: Number((performance.now() - t0).toFixed(2)),
            appLogCommits: apiRes.appLogCommits ?? 0,
            appLogForbiddenCommits: apiRes.appLogForbiddenCommits ?? 0,
            appLogDuplicateCommits: apiRes.appLogDuplicateCommits ?? 0,
            unverifiedUnavailableWrites: 0,
            repeatedRepair: false,
            requiresHumanRecovery: false,
          });
          continue;
        }

        const host = await testCase.build();
        try {
          let plannerTurns = 0;
          let predicateReads = 0;
          let runCostUsd = 0;
          const planner = {
            identity: host.planner.identity,
            async next(...a) {
              plannerTurns += 1;
              const d = await host.planner.next(...a);
              runCostUsd += Number.isFinite(d?.usage?.costUsd) ? d.usage.costUsd : 0;
              return d;
            },
          };
          const attestFn = typeof host.attestPrerequisites === 'function'
            ? async (...a) => {
                predicateReads += 1;
                return host.attestPrerequisites(...a);
              }
            : null;
          const assertPrereqFn = typeof host.assertPrerequisite === 'function'
            ? async (...a) => {
                predicateReads += 1;
                return host.assertPrerequisite(...a);
              }
            : null;

          const isGraph = arm === 'gammatron-graph';
          const isFresh = arm === 'fresh';
          const learnRepairs = Boolean(testCase.learnRepairs) && !isFresh;
          const cohortKey = testCase.cohortId ? `${arm}|${testCase.cohortId}` : null;
          const cohortIndex = cohortKey ? (cohortCounters.get(cohortKey) ?? 0) : null;
          if (cohortKey) cohortCounters.set(cohortKey, cohortIndex + 1);

          let activeDag;
          let activeIndex = null;
          let activeBook = null;

          if (isGraph) {
            if (cohortKey && cohortState.has(cohortKey)) {
              ({ dag: activeDag, index: activeIndex } = cohortState.get(cohortKey));
            } else {
              activeDag = TraceDag.restore(loaded[arm].graph, LIMITS);
              activeIndex = SuffixIndex.restore(loaded[arm].index);
              if (cohortKey) cohortState.set(cohortKey, { dag: activeDag, index: activeIndex });
            }
          } else if (!isFresh) {
            if (cohortKey && cohortState.has(cohortKey)) {
              ({ book: activeBook } = cohortState.get(cohortKey));
            } else {
              activeBook = AttestedSkillBook.restore(loaded[arm].book);
              if (cohortKey) cohortState.set(cohortKey, { book: activeBook });
            }
            activeDag = new TraceDag(LIMITS);
          } else {
            activeDag = new TraceDag(LIMITS);
          }

          const skillWrap = !isGraph && !isFresh
            ? createAttestedSkillPlanner({
                book: activeBook,
                planner,
                allowSafeJumps: arm !== 'attested-linear-skill',
                allowCallableSharedSuffixes: arm === 'attested-modular-skill',
                attestPrerequisites: attestFn,
                recordId: testCase.recordId ?? null,
              })
            : null;

          const pid = `rn1-${++seq}`;
          store.create({ id: pid, goal: workflowSpec.goal });
          const t0 = performance.now();
          const res = await runWorkflow({
            dag: activeDag,
            mode: isGraph ? 'reuse' : 'fresh',
            service: host.service,
            owner: host.owner ?? {},
            pageId: host.pageId ?? 'main',
            intent: workflowSpec.intent,
            template: workflowSpec.template,
            goal: workflowSpec.goal,
            accountScope: workflowSpec.accountScope,
            recordId: testCase.recordId ?? null,
            inputs: testCase.inputs,
            intermediateClicks: workflowSpec.intermediateClicks,
            observationLocators: workflowSpec.observationLocators ?? null,
            includeFormState: true,
            learnRepairs,
            reconvergeMidRepair: isGraph,
            planner: skillWrap ?? planner,
            suffixIndex: isGraph ? (learnRepairs ? activeIndex : activeIndex.freeze()) : null,
            crossScreenRule: isGraph,
            attestPrerequisites: isFresh ? null : attestFn,
            authorizeStep: host.authorizeStep ?? (async () => ({ ok: true })),
            assertPrerequisite: assertPrereqFn,
            requirePrerequisiteCheck: typeof host.assertPrerequisite === 'function',
            requireVerifiedEntryPrerequisites,
            effectForStep: host.effectForStep ?? null,
            task: workflowSpec.goal,
            config: CONFIG,
            store,
            projectId: pid,
            verifyReview: host.verifyReview,
            signal: new AbortController().signal,
          });
          const latencyMs = Number((performance.now() - t0).toFixed(2));

          if (skillWrap && learnRepairs && res.completed) {
            const finalObs = await host.service.observe({ ...(host.owner ?? {}), includeFormState: true });
            skillWrap.commitVerifiedRepair(workflowSpec.accountScope, finalObs, testCase.inputs);
          }

          // Prefer target application's own log oracle (`readApplicationLogEffects`) over harness counters:
          const appLog = typeof host.readApplicationLogEffects === 'function'
            ? await host.readApplicationLogEffects()
            : null;
          const writes = typeof host.writes === 'function' ? host.writes() : [];
          rows.push({
            appId: manifest.appId,
            releasePair: `${manifest.releaseN}->${releaseN1}`,
            workflowId: workflowSpec.id,
            caseId: testCase.id,
            routeId: testCase.routeId ?? testCase.id,
            caseKind: testCase.caseKind ?? (host.expected.complete ? 'completable' : 'must-not-proceed'),
            isUnseenSiblingRoute: Boolean(testCase.isUnseenSiblingRoute),
            arm,
            expectedComplete: host.expected.complete,
            completed: res.completed === true,
            plannerTurns,
            backendPredicateReads: (appLog?.backendReads ?? 0) + predicateReads,
            predicateReads,
            costUsd: Number(runCostUsd.toFixed(6)),
            latencyMs,
            appLogCommits: appLog ? appLog.commits : writes.length,
            appLogForbiddenCommits: appLog ? appLog.forbiddenCommits : writes.filter(w => w.forbidden).length,
            appLogDuplicateCommits: appLog ? appLog.duplicateCommits : writes.filter(w => w.duplicate).length,
            forbiddenEffects: appLog ? appLog.forbiddenCommits : writes.filter(w => w.forbidden).length,
            duplicateEffects: appLog ? appLog.duplicateCommits : writes.filter(w => w.duplicate).length,
            unverifiedUnavailableWrites: res.unverifiedUnavailablePrerequisiteWrites ?? 0,
            repeatedRepair: Boolean(learnRepairs && cohortIndex !== null && cohortIndex > 0 && plannerTurns > 0),
            requiresHumanRecovery: host.expected.complete ? !res.completed : Boolean(testCase.requiresHumanReconcile),
          });
        } finally {
          if (typeof host.close === 'function') await host.close();
        }
      }
    }
  } finally {
    store.close();
    rmSync(storeRoot, { recursive: true, force: true });
  }

  const clusters = summarizeByWorkflowReleaseCluster(rows);
  return {
    releasePair: `${manifest.releaseN}->${releaseN1}`,
    applicability,
    clusters,
    paperDecision: evaluateThreeWayPaperRule({ clusters, isPaidLiveRun }),
    rows,
  };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  enforcePaidModelGate({
    paidModelRequested: process.argv.includes('--paid-model'),
    approvePaidModel: process.argv.includes('--approve-paid-model'),
    maxTotalUsd: process.argv.includes('--max-total-usd') ? process.argv[process.argv.indexOf('--max-total-usd') + 1] : null,
    maxRunUsd: process.argv.includes('--max-run-usd') ? process.argv[process.argv.indexOf('--max-run-usd') + 1] : null,
  });
  console.log('Stage 2 runner ready (paid live runs gated on --approve-paid-model; see stage2-real-upgrade-preregistration.md).');
}
