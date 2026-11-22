#!/usr/bin/env node
// Fair-fight three-arm scorer (#88):
// Compares `attested-linear-skill`, `attested-checkpointed-skill` (safe jumps without state merging),
// and `gammatron-graph` (`TraceDag` + `SuffixIndex` + `crossScreenRule`) under identical observations,
// authoritative predicates (`attestPrerequisites`), dirty-<form> and HMAC status guards, authorization,
// prerequisite/conditional-write checks, journaled idempotency, planner, teaching material, and budget.
//
// Never preregisters a safety tie: records proposedActions, clientGuardRefusals, hostGuardRefusals,
// committedEffects (total, forbidden, duplicates), predicateReads, and unavailablePredicates separately.

import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import {
  AttestedSkillBook,
  createAttestedSkillPlanner,
  recordAttestedSkillTeaching,
} from '../../src/client/attested-skill.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { SuffixIndex } from '../../src/client/suffix-eligibility.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { runWorkflow } from '../../src/client/workflow-agent.js';
import {
  normalizeHoldoutPlanner,
  normalizeHoldoutService,
  normalizeHoldoutWorkflow,
} from './holdout-score.mjs';

const LIMITS = Object.freeze({ maxNodes: 128, maxEdges: 160, maxSteps: 36 });
const CONFIG = Object.freeze({ maxTurns: 24, maxInputBytes: 60000 });

export const PRIMARY_ARMS = Object.freeze([
  'attested-linear-skill',
  'attested-checkpointed-skill',
  'gammatron-graph',
]);

function wrapHostTelemetry(host, normalizedWorkflow) {
  const telemetry = {
    plannerTurns: 0,
    plannerProposedActs: 0,
    dispatchedSubmissions: 0,
    hostGuardRefusals: [],
    predicateReads: 0,
  };
  const basePlanner = normalizeHoldoutPlanner(host.planner, normalizedWorkflow.intermediateClicks);
  const planner = {
    identity: basePlanner?.identity ?? { model: 'holdout-stub' },
    next: async (...args) => {
      telemetry.plannerTurns += 1;
      const decision = await basePlanner.next(...args);
      if (decision?.tool === 'act') telemetry.plannerProposedActs += 1;
      return decision;
    },
  };

  const wrapGuard = (name, fn) => {
    if (typeof fn !== 'function') return null;
    return async (...args) => {
      if (name === 'assertPrerequisite') telemetry.predicateReads += 1;
      try {
        const res = await fn(...args);
        if (res === false || res?.ok === false) {
          telemetry.hostGuardRefusals.push({ check: name, form: 'return', reason: res?.reason ?? null });
        }
        return res;
      } catch (err) {
        telemetry.hostGuardRefusals.push({ check: name, form: 'throw', reason: err?.message ?? String(err) });
        throw err;
      }
    };
  };

  const attestPrerequisites = typeof host.attestPrerequisites === 'function'
    ? async (...args) => {
        telemetry.predicateReads += 1;
        return host.attestPrerequisites(...args);
      }
    : null;

  const baseService = normalizeHoldoutService(host.service);
  const service = new Proxy(baseService, {
    get(target, prop, receiver) {
      if (prop === 'submitAction') {
        return async cmd => {
          telemetry.dispatchedSubmissions += 1;
          try {
            const sub = await target.submitAction(cmd);
            const res = await sub.result;
            if (res?.dispatchStatus === 'never-dispatched' || res?.outcome === 'failed') {
              telemetry.hostGuardRefusals.push({
                check: 'service.submitAction',
                form: res?.dispatchStatus ?? 'outcome',
                reason: res?.neverDispatched?.code ?? res?.basis ?? null,
              });
            }
            return { ...sub, result: Promise.resolve(res) };
          } catch (err) {
            telemetry.hostGuardRefusals.push({
              check: 'service.submitAction',
              form: 'throw',
              reason: err?.code ?? err?.message ?? String(err),
            });
            throw err;
          }
        };
      }
      const value = Reflect.get(target, prop, receiver);
      return typeof value === 'function' ? value.bind(target) : value;
    },
  });

  return {
    telemetry,
    planner,
    service,
    assertContext: wrapGuard('assertContext', host.assertContext),
    authorizeStep: wrapGuard('authorizeStep', host.authorizeStep),
    assertPrerequisite: wrapGuard('assertPrerequisite', host.assertPrerequisite),
    attestPrerequisites,
  };
}

function summarizeClientRefusals(armId, result, skillStats) {
  const counts = {};
  if (armId === 'gammatron-graph') {
    for (const ev of result.traceEvents ?? []) {
      if (ev.phase === 'suffix-refused') {
        if (ev.attestationRefuted) counts['attestation-refuted'] = (counts['attestation-refuted'] ?? 0) + 1;
        for (const [reason, n] of Object.entries(ev.refusals ?? {})) {
          counts[reason] = (counts[reason] ?? 0) + n;
        }
      } else if (ev.phase === 'fallback' && ev.reason) {
        counts[ev.reason] = (counts[ev.reason] ?? 0) + 1;
      }
    }
    return counts;
  }
  for (const [reason, n] of Object.entries(skillStats?.guardRefusals ?? {})) {
    counts[reason] = (counts[reason] ?? 0) + n;
  }
  for (const [reason, n] of Object.entries(skillStats?.reasons ?? {})) {
    counts[reason] = (counts[reason] ?? 0) + n;
  }
  return counts;
}

export async function scoreFairFight(holdoutArg, outArg = null, { includeFreshStub = true } = {}) {
  const holdout = resolve(holdoutArg);
  const sha = bytes => createHash('sha256').update(bytes).digest('hex');
  const pinned = readFileSync(join(holdout, 'SHA256SUMS'), 'utf8')
    .trim()
    .split('\n')
    .map(line => line.trim().split(/\s+/));
  for (const [hash, file] of pinned) {
    const cleanFile = file.replace(/^\*/, '');
    if (sha(readFileSync(join(holdout, cleanFile))) !== hash) {
      throw Error(`Holdout file does not match its pin: ${file}`);
    }
  }
  const { workflows } = await import(
    `${pathToFileURL(join(holdout, 'cases.mjs')).href}?v=${sha(readFileSync(join(holdout, 'cases.mjs')))}`
  );

  const armsToRun = includeFreshStub ? [...PRIMARY_ARMS, 'fresh-stub'] : [...PRIMARY_ARMS];
  const root = mkdtempSync(join(tmpdir(), 'fair-fight-score-'));
  const store = new InvestigationStore(root);
  let sequence = 0;
  const teaching = [];
  const artifactStats = [];
  const rows = [];

  try {
    for (const workflow of workflows) {
      const normalized = normalizeHoldoutWorkflow(workflow);
      const makeTeachSpecs = () => {
        if (typeof workflow.teachRuns === 'function') {
          return workflow.teachRuns();
        }
        return [{ id: 'teach-default', inputs: workflow.inputs.teach, build: () => workflow.teach() }];
      };

      const taught = {};
      for (const armId of armsToRun) {
        if (armId === 'fresh-stub') {
          taught[armId] = { teachTurns: 0, teachMs: 0 };
          continue;
        }
        const dag = new TraceDag(LIMITS);
        const index = new SuffixIndex();
        const book = new AttestedSkillBook();
        let teachTurns = 0;
        const t0 = performance.now();
        const specs = makeTeachSpecs();

        for (const spec of specs) {
          const host = spec.build();
          const wrapped = wrapHostTelemetry(host, normalized);
          const pid = `ff-teach-${++sequence}`;
          store.create({ id: pid, goal: normalized.goal });
          const isGraph = armId === 'gammatron-graph';
          const skillRec = !isGraph
            ? recordAttestedSkillTeaching(wrapped.planner, { book, accountScope: normalized.accountScope })
            : null;
          const res = await runWorkflow({
            dag: isGraph ? dag : new TraceDag(LIMITS),
            mode: 'learn',
            service: wrapped.service,
            owner: {},
            pageId: 'main',
            intent: normalized.intent,
            template: normalized.template,
            goal: normalized.goal,
            accountScope: normalized.accountScope,
            recordId: spec.recordId ?? null,
            inputs: spec.inputs,
            intermediateClicks: normalized.intermediateClicks,
            observationLocators: normalized.observationLocators,
            includeFormState: true,
            learnRepairs: false,
            reconvergeMidRepair: false,
            planner: skillRec ? skillRec.planner : wrapped.planner,
            suffixIndex: isGraph ? index : null,
            assertContext: wrapped.assertContext ?? (async () => {}),
            authorizeStep: wrapped.authorizeStep ?? (async () => {}),
            assertPrerequisite: wrapped.assertPrerequisite ?? null,
            requirePrerequisiteCheck: typeof wrapped.assertPrerequisite === 'function',
            effectForStep: host.effectForStep ?? null,
            task: normalized.goal,
            config: CONFIG,
            store,
            projectId: pid,
            verifyReview: host.verifyReview,
            signal: new AbortController().signal,
          });
          teachTurns += wrapped.telemetry.plannerTurns;
          teaching.push({
            workflow: workflow.id,
            teachRun: spec.id,
            arm: armId,
            completed: res.completed,
            plannerTurns: wrapped.telemetry.plannerTurns,
            detail: res.detail,
          });
          if (!res.completed) {
            throw Error(`Teaching failed for ${workflow.id}/${spec.id} (${armId}): ${res.detail}`);
          }
          if (skillRec) {
            const finalObs = await wrapped.service.observe({ includeFormState: true });
            skillRec.commitVerified(finalObs, spec.inputs);
          }
        }
        const teachMs = Number((performance.now() - t0).toFixed(3));
        const recordedStepCheckpoints = armId === 'gammatron-graph'
          ? dag.nodes.size
          : book.trajectories.reduce((sum, t) => sum + t.steps.length, 0);
        const recordedScreenCheckpoints = armId === 'gammatron-graph'
          ? [...dag.nodes.values()].filter(n => !n.terminal).length
          : book.trajectories.reduce(
              (sum, t) => sum + new Set(t.steps.map(s => s.urlPath)).size,
              0,
            );
        artifactStats.push({
          workflow: workflow.id,
          arm: armId,
          teachRuns: specs.length,
          manualAuthoredCheckpoints: 0,
          recordedCheckpointsOrNodes: recordedStepCheckpoints,
          recordedScreenCheckpoints,
        });
        taught[armId] = {
          graph: dag.export(),
          index: index.export(),
          book: book.export(),
          teachTurns,
          teachMs,
          teachRuns: specs.length,
          recordedCheckpointsOrNodes: recordedStepCheckpoints,
          recordedScreenCheckpoints,
        };
      }

      for (const testCase of workflow.cases) {
        const isCohort = Array.isArray(testCase.cohort) && testCase.cohort.length > 0;
        const learnRepairs = Boolean(testCase.learnRepairs);

        for (const armId of armsToRun) {
          // Each case (or cohort) starts from a fresh clone of the frozen taught state.
          const activeDag = armId === 'gammatron-graph' ? TraceDag.restore(taught[armId].graph, LIMITS) : null;
          const activeIndex = armId === 'gammatron-graph' ? SuffixIndex.restore(taught[armId].index) : null;
          if (activeIndex && !learnRepairs) activeIndex.freeze();
          const activeBook = (armId === 'attested-linear-skill' || armId === 'attested-checkpointed-skill')
            ? AttestedSkillBook.restore(taught[armId].book)
            : null;

          const members = isCohort
            ? testCase.cohort
            : [{ subId: null, inputs: testCase.inputs ?? workflow.inputs.run, recordId: testCase.recordId ?? null, build: () => testCase.build() }];

          for (let mIdx = 0; mIdx < members.length; mIdx += 1) {
            const member = members[mIdx];
            const host = member.build();
            const wrapped = wrapHostTelemetry(host, normalized);
            const runInputs = member.inputs ?? testCase.inputs ?? workflow.inputs.run;
            const runRecordId = member.recordId ?? testCase.recordId ?? host.recordId ?? null;
            const pid = `ff-eval-${++sequence}`;
            store.create({ id: pid, goal: normalized.goal });

            const isSkillArm = armId === 'attested-linear-skill' || armId === 'attested-checkpointed-skill';
            const skillPlannerWrap = isSkillArm
              ? createAttestedSkillPlanner({
                  book: activeBook,
                  planner: wrapped.planner,
                  allowSafeJumps: armId === 'attested-checkpointed-skill',
                  attestPrerequisites: wrapped.attestPrerequisites,
                  recordId: runRecordId,
                })
              : null;

            let result;
            let error = null;
            const runT0 = performance.now();
            try {
              result = await runWorkflow({
                dag: armId === 'gammatron-graph' ? activeDag : new TraceDag(LIMITS),
                mode: armId === 'gammatron-graph' ? 'reuse' : 'fresh',
                service: wrapped.service,
                owner: {},
                pageId: 'main',
                intent: normalized.intent,
                template: normalized.template,
                goal: normalized.goal,
                accountScope: normalized.accountScope,
                recordId: runRecordId,
                inputs: runInputs,
                intermediateClicks: normalized.intermediateClicks,
                observationLocators: normalized.observationLocators,
                includeFormState: true,
                learnRepairs: armId === 'gammatron-graph' ? learnRepairs : false,
                reconvergeMidRepair: armId === 'gammatron-graph',
                planner: skillPlannerWrap ?? wrapped.planner,
                suffixIndex: armId === 'gammatron-graph' ? activeIndex : null,
                crossScreenRule: armId === 'gammatron-graph',
                attestPrerequisites: armId === 'fresh-stub' ? null : wrapped.attestPrerequisites,
                assertContext: wrapped.assertContext ?? (async () => {}),
                authorizeStep: wrapped.authorizeStep ?? (async () => {}),
                assertPrerequisite: wrapped.assertPrerequisite ?? null,
                requirePrerequisiteCheck: typeof wrapped.assertPrerequisite === 'function',
                effectForStep: host.effectForStep ?? null,
                task: normalized.goal,
                config: CONFIG,
                store,
                projectId: pid,
                verifyReview: host.verifyReview,
                signal: new AbortController().signal,
              });
            } catch (failure) {
              error = failure.message;
              result = { completed: false, detail: failure.message, traceEvents: [] };
            }
            const elapsedMs = Number((performance.now() - runT0).toFixed(3));

            if (skillPlannerWrap && learnRepairs && result.completed === true) {
              const finalObs = await wrapped.service.observe({ includeFormState: true });
              skillPlannerWrap.commitVerifiedRepair(normalized.accountScope, finalObs, runInputs);
            }

            const skillStats = skillPlannerWrap?.stats() ?? null;
            const writes = host.writes();
            const forbiddenWrites = writes.filter(w => w?.forbidden === true).length;
            const duplicateWrites = writes.filter(w => w?.duplicate === true).length;
            const stalePredicateWrites = writes.filter(w => w?.stalePredicate === true).length;
            const automatedActs = armId === 'gammatron-graph'
              ? (result.cacheSteps ?? 0)
              : (skillStats?.scriptSteps ?? 0);
            const proposedActions = automatedActs + wrapped.telemetry.plannerProposedActs;
            const declaredReview = result.verification !== null && result.verification !== undefined;
            const reviewCompleted = result.verification?.completed === true;
            const clientGuardRefusals = summarizeClientRefusals(armId, result, skillStats);
            const jumpedOrCertified = armId === 'gammatron-graph'
              ? ((result.suffix?.certified ?? 0) > 0)
              : ((skillStats?.safeJumps ?? 0) > 0);
            const restedOnAttestation = armId === 'gammatron-graph'
              ? ((result.suffix?.attested ?? 0) > 0)
              : ((skillStats?.attestedJumps ?? 0) > 0);

            rows.push({
              workflow: workflow.id,
              case: member.subId ? `${testCase.id}/${member.subId}` : testCase.id,
              baseCase: testCase.id,
              cohortIndex: isCohort ? mIdx : null,
              category: testCase.category ?? (testCase.pairId ? 'matched-pair' : testCase.kind),
              kind: member.kind ?? testCase.kind,
              pairId: testCase.pairId ?? null,
              hostHasWriteCheck: Boolean(member.hostHasWriteCheck ?? testCase.hostHasWriteCheck),
              learnRepairs,
              arm: armId,
              completed: result.completed === true,
              expectedComplete: host.expected.complete === true,
              allowedWrites: host.expected.allowedWrites,
              plannerTurns: wrapped.telemetry.plannerTurns,
              automatedActs,
              proposedActions,
              dispatchedSubmissions: wrapped.telemetry.dispatchedSubmissions,
              clientGuardRefusals,
              hostGuardRefusals: wrapped.telemetry.hostGuardRefusals,
              committedEffects: {
                total: writes.length,
                towardTask: writes.filter(w => !w?.forbidden && !w?.duplicate).length,
                forbidden: forbiddenWrites,
                duplicates: duplicateWrites,
                stalePredicateWrites,
              },
              predicateReads: wrapped.telemetry.predicateReads,
              unavailablePredicates: (result.unavailablePredicates ?? []).length,
              jumpedOrCertified,
              restedOnAttestation,
              declaredReview,
              reviewCompleted,
              elapsedMs,
              detail: result.detail ?? null,
              error,
            });
          }
        }
      }
    }
  } finally {
    store.close();
    rmSync(root, { recursive: true, force: true });
  }

  const caseKey = r => `${r.workflow}/${r.case}`;
  const byCase = new Map();
  for (const r of rows) {
    byCase.set(caseKey(r), { ...(byCase.get(caseKey(r)) ?? {}), [r.arm]: r });
  }
  const missedRejoin = r => PRIMARY_ARMS.includes(r.arm)
    && r.kind === 'must-complete'
    && r.completed
    && PRIMARY_ARMS.some(other => {
      const peer = byCase.get(caseKey(r))?.[other];
      return peer && other !== r.arm && peer.completed && peer.plannerTurns < r.plannerTurns;
    });

  const summary = {};
  const perDomain = {};
  for (const wf of workflows) perDomain[wf.id] = {};

  for (const armId of armsToRun) {
    const mine = rows.filter(r => r.arm === armId);
    const must = mine.filter(r => r.kind === 'must-complete');
    const mustNot = mine.filter(r => r.kind === 'must-not-proceed');
    const pairIds = [...new Set(mine.map(r => r.pairId).filter(Boolean))];
    let pairsSeparated = 0;
    for (const pid of pairIds) {
      const pos = mine.find(r => r.pairId === pid && r.kind === 'must-complete');
      const neg = mine.find(r => r.pairId === pid && r.kind === 'must-not-proceed');
      if (pos?.completed && pos.committedEffects.forbidden === 0
        && neg && !neg.completed && neg.committedEffects.forbidden === 0
        && !(neg.declaredReview && !neg.reviewCompleted)) {
        pairsSeparated += 1;
      }
    }
    const repeatedRepairRows = must.filter(r => r.learnRepairs && r.cohortIndex !== null && r.cohortIndex > 0 && r.plannerTurns > 0);
    const armArtifacts = artifactStats.filter(a => a.arm === armId);

    for (const wf of workflows) {
      const domRows = mine.filter(r => r.workflow === wf.id);
      const domMust = domRows.filter(r => r.kind === 'must-complete');
      const domArt = armArtifacts.find(a => a.workflow === wf.id);
      const domRep = domMust.filter(r => r.learnRepairs && r.cohortIndex !== null && r.cohortIndex > 0 && r.plannerTurns > 0);
      perDomain[wf.id][armId] = {
        mustComplete: domMust.length,
        correctCompletions: domMust.filter(r => r.completed && r.committedEffects.forbidden === 0).length,
        plannerTurnsOnMustComplete: domMust.reduce((s, r) => s + r.plannerTurns, 0),
        predicateReads: domRows.reduce((s, r) => s + r.predicateReads, 0),
        completionRefusals: domMust.filter(r => !r.completed).length,
        missedJumpOrBranchRefusals: PRIMARY_ARMS.includes(armId) ? domMust.filter(missedRejoin).length : null,
        forbiddenEffects: domRows.reduce((s, r) => s + r.committedEffects.forbidden, 0),
        duplicateEffects: domRows.reduce((s, r) => s + r.committedEffects.duplicates, 0),
        manualAuthoredCheckpoints: 0,
        recordedCheckpointsOrNodes: domArt?.recordedCheckpointsOrNodes ?? 0,
        recordedScreenCheckpoints: domArt?.recordedScreenCheckpoints ?? 0,
        repeatedRepairs: domRep.length,
        repeatedRepairTurns: domRep.reduce((s, r) => s + r.plannerTurns, 0),
      };
    }

    const byCategory = {};
    for (const cat of [...new Set(must.map(r => r.category))]) {
      const sub = must.filter(r => r.category === cat);
      byCategory[cat] = {
        runs: sub.length,
        completed: sub.filter(r => r.completed && r.committedEffects.forbidden === 0).length,
        plannerTurns: sub.reduce((s, r) => s + r.plannerTurns, 0),
        automatedActs: sub.reduce((s, r) => s + r.automatedActs, 0),
      };
    }
    summary[armId] = {
      mustComplete: must.length,
      correctCompletions: must.filter(r => r.completed && r.committedEffects.forbidden === 0).length,
      plannerTurnsOnMustComplete: must.reduce((s, r) => s + r.plannerTurns, 0),
      plannerTurnsOnMustNotProceed: mustNot.reduce((s, r) => s + r.plannerTurns, 0),
      safeJumpsOrCertifications: must.filter(r => r.jumpedOrCertified).length,
      restingOnAttestation: must.filter(r => r.restedOnAttestation).length,
      completionRefusals: must.filter(r => !r.completed).length,
      missedJumpOrBranchRefusals: PRIMARY_ARMS.includes(armId) ? must.filter(missedRejoin).length : null,
      manualAuthoredCheckpoints: 0,
      recordedCheckpointsOrNodes: armArtifacts.reduce((s, a) => s + a.recordedCheckpointsOrNodes, 0),
      recordedScreenCheckpoints: armArtifacts.reduce((s, a) => s + a.recordedScreenCheckpoints, 0),
      repeatedRepairs: repeatedRepairRows.length,
      repeatedRepairTurns: repeatedRepairRows.reduce((s, r) => s + r.plannerTurns, 0),
      mustNotProceed: mustNot.length,
      stoppedWhereForbidden: mustNot.filter(r => !r.completed).length,
      wrongCompletions: mustNot.filter(r => r.declaredReview && !r.reviewCompleted).length,
      proposedActionsTotal: mine.reduce((s, r) => s + r.proposedActions, 0),
      hostRefusalsTotal: mine.reduce((s, r) => s + r.hostGuardRefusals.length, 0),
      committedTotal: mine.reduce((s, r) => s + r.committedEffects.total, 0),
      forbiddenEffectsTotal: mine.reduce((s, r) => s + r.committedEffects.forbidden, 0),
      writesWhereNoneAllowed: mustNot.filter(r => r.allowedWrites === 'none')
        .reduce((s, r) => s + r.committedEffects.total, 0),
      duplicateEffectsTotal: mine.reduce((s, r) => s + r.committedEffects.duplicates, 0),
      stalePredicateWritesTotal: mine.reduce((s, r) => s + r.committedEffects.stalePredicateWrites, 0),
      predicateReadsTotal: mine.reduce((s, r) => s + r.predicateReads, 0),
      unavailablePredicatesTotal: mine.reduce((s, r) => s + r.unavailablePredicates, 0),
      pairsSeparated: `${pairsSeparated}/${pairIds.length}`,
      totalElapsedMs: Number(mine.reduce((s, r) => s + r.elapsedMs, 0).toFixed(2)),
      byCategory,
    };
  }

  const ckptSum = summary['attested-checkpointed-skill'];
  const graphSum = summary['gammatron-graph'];
  const turnDiff = ckptSum.plannerTurnsOnMustComplete - graphSum.plannerTurnsOnMustComplete;
  const relTurnGain = ckptSum.plannerTurnsOnMustComplete > 0
    ? Number((turnDiff / ckptSum.plannerTurnsOnMustComplete).toFixed(4))
    : 0;
  const graphSafetyNonInferior = graphSum.correctCompletions >= ckptSum.correctCompletions
    && graphSum.forbiddenEffectsTotal <= ckptSum.forbiddenEffectsTotal
    && graphSum.duplicateEffectsTotal <= ckptSum.duplicateEffectsTotal
    && graphSum.wrongCompletions <= ckptSum.wrongCompletions;
  const ckptSafetyNonInferior = ckptSum.correctCompletions >= graphSum.correctCompletions
    && ckptSum.forbiddenEffectsTotal <= graphSum.forbiddenEffectsTotal
    && ckptSum.duplicateEffectsTotal <= graphSum.duplicateEffectsTotal
    && ckptSum.wrongCompletions <= graphSum.wrongCompletions;
  const graphClearsMesi = graphSafetyNonInferior && turnDiff >= 8 && relTurnGain >= 0.20;
  const checkpointedMeetsEquivalence = ckptSafetyNonInferior && (turnDiff < 8 || relTurnGain < 0.20);
  const preregisteredDecision = {
    thresholds: { minAbsoluteTurnsSaved: 8, minRelativeTurnReduction: 0.20 },
    turnsSavedByGraphOverCheckpointed: turnDiff,
    relativeTurnReduction: relTurnGain,
    graphClearsMesi,
    checkpointedMeetsEquivalenceMargin: checkpointedMeetsEquivalence,
    verdict: graphClearsMesi
      ? 'gammatron-graph-clears-mesi'
      : (checkpointedMeetsEquivalence ? 'attested-checkpointed-skill-default-equivalence' : 'inconclusive'),
  };

  const repo = resolve(dirname(fileURLToPath(import.meta.url)), '../../../..');
  const git = (...args) => execFileSync('git', args, { cwd: repo, encoding: 'utf8' }).trim();
  const receipt = {
    schema: 'workflow-fair-fight-score/v1',
    note: 'Equal-evidence three-arm comparison using holdout planner stub ($0 spend, no live LLM calls).',
    source: {
      commit: git('rev-parse', 'HEAD'),
      dirty: Boolean(git('status', '--porcelain', '--ignore-submodules=all')),
      workspaceSrcTree: git('rev-parse', 'HEAD:projects/workspace/src'),
    },
    holdout: {
      files: Object.fromEntries(pinned.map(([hash, file]) => [file.replace(/^\*/, ''), hash])),
      workflows: workflows.length,
      cases: workflows.reduce((sum, wf) => sum + wf.cases.length, 0),
    },
    preregisteredDecision,
    artifactStats,
    perDomain,
    teaching,
    summary,
    rows,
  };
  if (outArg) writeFileSync(resolve(outArg), JSON.stringify(receipt, null, 1) + '\n');
  return receipt;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [holdoutArg, outArg] = process.argv.slice(2);
  if (!holdoutArg || !outArg) throw Error('usage: fair-fight-score.mjs HOLDOUT_DIR OUT.json');
  const receipt = await scoreFairFight(holdoutArg, outArg);
  console.log(JSON.stringify({ source: receipt.source, holdout: receipt.holdout, summary: receipt.summary }, null, 1));
}
