#!/usr/bin/env node
// Post-v3 new-revision evaluation (#88):
//   - Keeps `blind-holdout-v3/` (`b46275121`) and `receipts/blind-holdout-v3-receipt.json` frozen.
//   - Evaluates 5 arms (`attested-linear-skill`, `attested-checkpointed-skill`, `attested-modular-skill`
//     with callable shared suffixes & repair reuse, `gammatron-graph`, and `fresh-stub`) at $0 spend across:
//       1. `v3DiagnosticPermissive`: post-v3 diagnostic rerun of the 36 cases (39 runs/arm) on the new
//          revision (`requireVerifiedEntryPrerequisites: false`, matching v3 host harness; NOT a blind score).
//       2. `v3HubWriteGateStrict`: the 6 `alternate-entry` cases of v3 under `requireVerifiedEntryPrerequisites: true`
//          (with and without live `assertPrerequisite({ verifiedUnavailable: true })`), verifying that
//          untaken-branch `holds: false` never refutes the taken branch AND an `unavailable` prerequisite
//          cannot authorize a write.
//       3. `modularVsGraphSeparation`: 9-case controlled comparison isolating where `attested-modular-skill`
//          matches `gammatron-graph` (screen-factored shared suffixes & repair reuse) vs. where `TraceDag` +
//          Bellman DP separates (multi-exit hub downstream-slot/goal routing and intra-screen state merge).

import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
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

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '../../../..');
const LIMITS = Object.freeze({ maxNodes: 128, maxEdges: 160, maxSteps: 36 });
const CONFIG = Object.freeze({ maxTurns: 24, maxInputBytes: 60000 });
const OWNER = Object.freeze({ callerId: 'modular-rev4-eval', surfaceId: 'eval' });

export const ARMS = Object.freeze([
  'attested-linear-skill',
  'attested-checkpointed-skill',
  'attested-modular-skill',
  'gammatron-graph',
  'fresh-stub',
]);

function wrapHost(host, normalizedWf) {
  const telemetry = {
    plannerTurns: 0,
    plannerProposedActs: 0,
    dispatchedSubmissions: 0,
    hostGuardRefusals: [],
    predicateReads: 0,
  };
  const basePlanner = normalizeHoldoutPlanner(host.planner, normalizedWf.intermediateClicks);
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
  const service = normalizeHoldoutService(host.service);
  return {
    telemetry,
    planner,
    service,
    assertContext: wrapGuard('assertContext', host.assertContext),
    authorizeStep: wrapGuard('authorizeStep', host.authorizeStep),
    assertPrerequisite: wrapGuard('assertPrerequisite', host.assertPrerequisite),
    attestPrerequisites,
    verifyReview: host.verifyReview,
  };
}

async function runSingleArmCase({
  armId,
  wf,
  normalizedWf,
  host,
  inputs,
  recordId,
  learnRepairs = false,
  requireVerifiedEntryPrerequisites = false,
  overrideAssertPrerequisite = null,
  dag,
  suffixIndex,
  book,
  store,
  mkProj,
}) {
  const wrapped = wrapHost(host, normalizedWf);
  const pid = mkProj(armId.slice(0, 6));
  const common = {
    service: wrapped.service,
    owner: OWNER,
    pageId: pid,
    intent: normalizedWf.intent,
    template: normalizedWf.template,
    goal: normalizedWf.goal,
    accountScope: normalizedWf.accountScope,
    recordId: recordId ?? null,
    inputs,
    intermediateClicks: normalizedWf.intermediateClicks,
    observationLocators: normalizedWf.observationLocators,
    task: normalizedWf.intent,
    config: CONFIG,
    store,
    projectId: pid,
    verifyReview: wrapped.verifyReview,
    signal: new AbortController().signal,
    includeFormState: true,
    ...(wrapped.assertContext ? { assertContext: wrapped.assertContext } : {}),
    ...(wrapped.authorizeStep ? { authorizeStep: wrapped.authorizeStep } : {}),
    ...(overrideAssertPrerequisite
      ? { assertPrerequisite: overrideAssertPrerequisite }
      : (wrapped.assertPrerequisite ? { assertPrerequisite: wrapped.assertPrerequisite } : {})),
    requireVerifiedEntryPrerequisites,
  };

  let res = null;
  let error = null;
  let automatedActs = 0;
  let clientGuardRefusals = {};
  let jumpedOrCertified = false;
  let sharedSuffixCalls = 0;

  try {
    if (armId === 'gammatron-graph') {
      res = await runWorkflow({
        ...common,
        dag,
        mode: 'reuse',
        planner: wrapped.planner,
        learnRepairs: Boolean(learnRepairs),
        reconvergeMidRepair: true,
        suffixIndex: learnRepairs ? suffixIndex : suffixIndex.freeze(),
        crossScreenRule: true,
        attestPrerequisites: wrapped.attestPrerequisites,
      });
      automatedActs = res.cacheSteps ?? 0;
      jumpedOrCertified = (res.suffix?.certified ?? 0) > 0;
      clientGuardRefusals = { ...(res.suffix?.refusals ?? {}) };
      if ((res.suffix?.attestationRefuted ?? 0) > 0) {
        clientGuardRefusals['attestation-refuted'] = res.suffix.attestationRefuted;
      }
    } else if (armId === 'fresh-stub') {
      res = await runWorkflow({
        ...common,
        dag: new TraceDag(LIMITS),
        mode: 'fresh',
        planner: wrapped.planner,
      });
    } else {
      const sp = createAttestedSkillPlanner({
        book,
        planner: wrapped.planner,
        allowSafeJumps: armId !== 'attested-linear-skill',
        allowCallableSharedSuffixes: armId === 'attested-modular-skill',
        attestPrerequisites: wrapped.attestPrerequisites,
        recordId: recordId ?? null,
      });
      res = await runWorkflow({
        ...common,
        dag: new TraceDag(LIMITS),
        mode: 'fresh',
        planner: sp,
      });
      const st = sp.stats();
      automatedActs = st.scriptSteps;
      jumpedOrCertified = st.safeJumps > 0;
      sharedSuffixCalls = st.sharedSuffixCalls ?? 0;
      clientGuardRefusals = { ...st.guardRefusals };
      if (learnRepairs && res.completed) {
        const finalObs = await wrapped.service.observe({ includeFormState: true });
        sp.commitVerifiedRepair(normalizedWf.accountScope, finalObs, inputs);
      }
    }
  } catch (err) {
    error = err?.code ?? err?.message ?? String(err);
  }

  const writes = typeof host.writes === 'function' ? host.writes() : [];
  const rev = await host.verifyReview();
  return {
    arm: armId,
    completed: Boolean(res?.completed && !error),
    plannerTurns: wrapped.telemetry.plannerTurns,
    automatedActs,
    proposedActions: automatedActs + wrapped.telemetry.plannerProposedActs,
    committedEffects: {
      total: writes.length,
      forbidden: writes.filter(w => w?.forbidden).length,
      duplicates: writes.filter(w => w?.duplicate).length,
    },
    predicateReads: wrapped.telemetry.predicateReads,
    unavailablePredicates: res?.unavailablePredicates?.length ?? 0,
    unverifiedUnavailablePrerequisiteWrites: res?.unverifiedUnavailablePrerequisiteWrites ?? 0,
    jumpedOrCertified,
    sharedSuffixCalls,
    clientGuardRefusals,
    hostGuardRefusals: wrapped.telemetry.hostGuardRefusals,
    reviewCompleted: Boolean(rev?.completed),
    detail: res?.detail ?? null,
    error,
  };
}

async function runPostV3Diagnostics(store, mkProj) {
  const holdoutUrl = pathToFileURL(join(HERE, 'blind-holdout-v3/cases.mjs')).href;
  const { workflows } = await import(holdoutUrl);

  const artifacts = new Map();
  for (const wf of workflows) {
    const normalizedWf = normalizeHoldoutWorkflow(wf);
    const dag = new TraceDag(LIMITS);
    const suffixIndex = new SuffixIndex();
    const linearBook = new AttestedSkillBook();
    const ckptBook = new AttestedSkillBook();
    const modBook = new AttestedSkillBook();

    for (const tr of wf.teachRuns()) {
      // Teach DAG
      {
        const host = tr.build();
        const wrapped = wrapHost(host, normalizedWf);
        const pid = mkProj('tdag');
        const res = await runWorkflow({
          dag,
          mode: 'learn',
          service: wrapped.service,
          owner: OWNER,
          pageId: pid,
          intent: normalizedWf.intent,
          template: normalizedWf.template,
          goal: normalizedWf.goal,
          accountScope: normalizedWf.accountScope,
          recordId: tr.recordId ?? null,
          inputs: tr.inputs,
          intermediateClicks: normalizedWf.intermediateClicks,
          observationLocators: normalizedWf.observationLocators,
          task: normalizedWf.intent,
          planner: wrapped.planner,
          config: CONFIG,
          store,
          projectId: pid,
          verifyReview: wrapped.verifyReview,
          signal: new AbortController().signal,
          suffixIndex,
          includeFormState: true,
        });
        if (!res.completed) throw Error(`DAG teach failed on ${wf.id}/${tr.id}`);
      }
      // Teach skill books identically from the exact same `teachRuns()`
      for (const b of [linearBook, ckptBook, modBook]) {
        const host = tr.build();
        const wrapped = wrapHost(host, normalizedWf);
        const rec = recordAttestedSkillTeaching(wrapped.planner, {
          book: b,
          accountScope: normalizedWf.accountScope,
        });
        const pid = mkProj('tskl');
        const res = await runWorkflow({
          dag: new TraceDag(LIMITS),
          mode: 'fresh',
          service: wrapped.service,
          owner: OWNER,
          pageId: pid,
          intent: normalizedWf.intent,
          template: normalizedWf.template,
          goal: normalizedWf.goal,
          accountScope: normalizedWf.accountScope,
          recordId: tr.recordId ?? null,
          inputs: tr.inputs,
          intermediateClicks: normalizedWf.intermediateClicks,
          observationLocators: normalizedWf.observationLocators,
          task: normalizedWf.intent,
          planner: rec.planner,
          config: CONFIG,
          store,
          projectId: pid,
          verifyReview: wrapped.verifyReview,
          signal: new AbortController().signal,
          includeFormState: true,
        });
        if (!res.completed) throw Error(`Skill teach failed on ${wf.id}/${tr.id}`);
        rec.commitVerified(await wrapped.service.observe({ includeFormState: true }), tr.inputs);
      }
    }
    artifacts.set(wf.id, { wf, normalizedWf, dag, suffixIndex, linearBook, ckptBook, modBook });
  }

  // Slice 1: Permissive post-v3 diagnostic across all 36 cases (39 runs x 5 arms)
  const rows = [];
  for (const { wf, normalizedWf, dag, suffixIndex, linearBook, ckptBook, modBook } of artifacts.values()) {
    for (const c of wf.cases) {
      for (const armId of ARMS) {
        if (Array.isArray(c.cohort)) {
          const mutDag = TraceDag.restore(dag.export(), LIMITS);
          const mutIdx = SuffixIndex.restore(suffixIndex.export());
          const mutBook = armId === 'attested-linear-skill'
            ? AttestedSkillBook.restore(linearBook.export())
            : (armId === 'attested-checkpointed-skill'
                ? AttestedSkillBook.restore(ckptBook.export())
                : AttestedSkillBook.restore(modBook.export()));
          for (let idx = 0; idx < c.cohort.length; idx += 1) {
            const m = c.cohort[idx];
            const host = m.build();
            const r = await runSingleArmCase({
              armId,
              wf,
              normalizedWf,
              host,
              inputs: m.inputs ?? wf.inputs.run,
              recordId: m.recordId,
              learnRepairs: Boolean(c.learnRepairs),
              dag: mutDag,
              suffixIndex: mutIdx,
              book: mutBook,
              store,
              mkProj,
            });
            rows.push({
              workflow: wf.id,
              case: `${c.id}/${m.subId}`,
              category: c.category,
              kind: m.kind ?? c.kind,
              learnRepairs: Boolean(c.learnRepairs),
              cohortIndex: idx,
              ...r,
            });
          }
        } else {
          const host = c.build();
          const r = await runSingleArmCase({
            armId,
            wf,
            normalizedWf,
            host,
            inputs: c.inputs ?? wf.inputs.run,
            recordId: c.recordId,
            learnRepairs: Boolean(c.learnRepairs),
            dag: TraceDag.restore(dag.export(), LIMITS),
            suffixIndex: SuffixIndex.restore(suffixIndex.export()),
            book: armId === 'attested-linear-skill'
              ? AttestedSkillBook.restore(linearBook.export())
              : (armId === 'attested-checkpointed-skill'
                  ? AttestedSkillBook.restore(ckptBook.export())
                  : AttestedSkillBook.restore(modBook.export())),
            store,
            mkProj,
          });
          rows.push({
            workflow: wf.id,
            case: c.id,
            category: c.category,
            kind: c.kind,
            learnRepairs: Boolean(c.learnRepairs),
            cohortIndex: null,
            ...r,
          });
        }
      }
    }
  }

  const summary = {};
  for (const armId of ARMS) {
    const mine = rows.filter(r => r.arm === armId);
    const must = mine.filter(r => r.kind === 'must-complete');
    const byCat = {};
    for (const cat of ['straightforward', 'alternate-entry', 'reconverging-branch']) {
      const sub = must.filter(r => r.category === cat);
      byCat[cat] = {
        completed: sub.filter(r => r.completed && r.committedEffects.forbidden === 0).length,
        runs: sub.length,
        plannerTurns: sub.reduce((s, r) => s + r.plannerTurns, 0),
        automatedActs: sub.reduce((s, r) => s + r.automatedActs, 0),
      };
    }
    const repRows = must.filter(r => r.learnRepairs && r.cohortIndex === 1 && r.plannerTurns > 0);
    let recordedUnits = 0;
    for (const a of artifacts.values()) {
      if (armId === 'gammatron-graph') recordedUnits += a.dag.nodes.size;
      else if (armId === 'attested-modular-skill') recordedUnits += a.modBook.compiledSubroutineStats().deduplicatedSteps;
      else if (armId === 'attested-checkpointed-skill') recordedUnits += a.ckptBook.trajectories.reduce((s, t) => s + t.steps.length, 0);
      else if (armId === 'attested-linear-skill') recordedUnits += a.linearBook.trajectories.reduce((s, t) => s + t.steps.length, 0);
    }
    summary[armId] = {
      correctCompletions: must.filter(r => r.completed && r.committedEffects.forbidden === 0).length,
      mustComplete: must.length,
      plannerTurnsOnMustComplete: must.reduce((s, r) => s + r.plannerTurns, 0),
      repeatedRepairs: repRows.length,
      repeatedRepairTurns: repRows.reduce((s, r) => s + r.plannerTurns, 0),
      recordedNodesOrDedupSteps: recordedUnits,
      predicateReadsTotal: mine.reduce((s, r) => s + r.predicateReads, 0),
      committedTotal: mine.reduce((s, r) => s + r.committedEffects.total, 0),
      forbiddenEffectsTotal: mine.reduce((s, r) => s + r.committedEffects.forbidden, 0),
      duplicateEffectsTotal: mine.reduce((s, r) => s + r.committedEffects.duplicates, 0),
      unverifiedUnavailableWritesTotal: mine.reduce((s, r) => s + r.unverifiedUnavailablePrerequisiteWrites, 0),
      byCategory: byCat,
    };
  }

  // Slice 2: Strict write-authorization check (`requireVerifiedEntryPrerequisites: true`) on the 6 `alternate-entry` cases
  const strictRows = [];
  for (const { wf, normalizedWf, dag, suffixIndex, linearBook, ckptBook, modBook } of artifacts.values()) {
    const altCases = wf.cases.filter(c => c.category === 'alternate-entry');
    for (const c of altCases) {
      for (const armId of ['attested-linear-skill', 'attested-checkpointed-skill', 'attested-modular-skill', 'gammatron-graph']) {
        const host = c.build();
        const r = await runSingleArmCase({
          armId,
          wf,
          normalizedWf,
          host,
          inputs: c.inputs ?? wf.inputs.run,
          recordId: c.recordId,
          requireVerifiedEntryPrerequisites: true,
          dag: TraceDag.restore(dag.export(), LIMITS),
          suffixIndex: SuffixIndex.restore(suffixIndex.export()),
          book: armId === 'attested-linear-skill'
            ? AttestedSkillBook.restore(linearBook.export())
            : (armId === 'attested-checkpointed-skill'
                ? AttestedSkillBook.restore(ckptBook.export())
                : AttestedSkillBook.restore(modBook.export())),
          store,
          mkProj,
        });
        strictRows.push({ workflow: wf.id, case: c.id, liveVerified: false, ...r });
      }
      // Also verify that explicit live verification (`verifiedUnavailable: true`) authorizes completion on the unavailable cases:
      if (c.id.includes('unavailable')) {
        for (const armId of ['attested-modular-skill', 'gammatron-graph']) {
          const host = c.build();
          const r = await runSingleArmCase({
            armId,
            wf,
            normalizedWf,
            host,
            inputs: c.inputs ?? wf.inputs.run,
            recordId: c.recordId,
            requireVerifiedEntryPrerequisites: true,
            overrideAssertPrerequisite: async () => ({ ok: true, verifiedUnavailable: true }),
            dag: TraceDag.restore(dag.export(), LIMITS),
            suffixIndex: SuffixIndex.restore(suffixIndex.export()),
            book: AttestedSkillBook.restore(modBook.export()),
            store,
            mkProj,
          });
          strictRows.push({ workflow: wf.id, case: c.id, liveVerified: true, ...r });
        }
      }
    }
  }

  return { permissiveSummary: summary, strictAlternateEntryRows: strictRows };
}

// Slice 3: Controlled 9-case separation benchmark (`attested-modular-skill` vs. `gammatron-graph`)
async function runModularVsGraphSeparation(store, mkProj) {
  function el(role, label, tag, inputType, handle, value = '', extra = {}) {
    const isCtrl = tag === 'input' || tag === 'select' || tag === 'textarea';
    return {
      role,
      label,
      tag,
      inputType,
      handle,
      selector: `#${handle}`,
      digest: `d-${handle}-${value}-${extra.text ?? ''}`,
      value,
      text: extra.text ?? (tag === 'button' ? label : ''),
      actionability: { visible: true, inert: false, disabled: false },
      formKey: isCtrl ? 'form-sep' : null,
      isDefaultValue: isCtrl ? value === '' : true,
    };
  }

  const domains = ['clinical-trial-dosing', 'satellite-pass-commanding', 'maritime-ballast-treatment'];
  const separationRows = [];

  for (const dom of domains) {
    const observationLocators = [
      ['textbox', 'Intake A1 Field', 'input', 'text'],
      ['textbox', 'Intake A2 Field', 'input', 'text'],
      ['button', 'To Shared Hub', 'button', ''],
      ['textbox', 'Hub Record Code', 'input', 'text'],
      ['button', 'Open Track B1', 'button', ''],
      ['button', 'Open Track B2', 'button', ''],
      ['textbox', 'Track B1 Param', 'input', 'text'],
      ['textbox', 'Track B2 Param', 'input', 'text'],
      ['button', 'To Downstream', 'button', ''],
      ['textbox', 'Added Safety Token', 'input', 'text'],
      ['textbox', 'Final Signoff', 'input', 'text'],
      ['button', 'Open Review', 'button', ''],
      ['status', 'Review Summary', 'output', ''],
    ];
    const intermediateClicks = [
      ['button', 'To Shared Hub', 'button', ''],
      ['button', 'Open Track B1', 'button', ''],
      ['button', 'Open Track B2', 'button', ''],
      ['button', 'To Downstream', 'button', ''],
      ['button', 'Open Review', 'button', ''],
    ];
    const mkInp = tag => ({
      a1: `A1-${dom}-${tag}`,
      a2: `A2-${dom}-${tag}`,
      hub: `HUB-${dom}-${tag}`,
      b1: `B1-${dom}-${tag}`,
      b2: `B2-${dom}-${tag}`,
      added: `ADD-${dom}-${tag}`,
      fin: `FIN-${dom}-${tag}`,
    });

    function buildSite({ branchA, branchB, multiExitHub, driftD, inputs }) {
      let screen = branchA;
      let ver = 0;
      const state = { a1: '', a2: '', hub: '', b1: '', b2: '', added: '', fin: '' };
      const writes = [];
      const render = () => {
        if (screen === 'a1') return [el('textbox', 'Intake A1 Field', 'input', 'text', 'h-a1', state.a1), el('button', 'To Shared Hub', 'button', '', 'h-go-hub')];
        if (screen === 'a2') return [el('textbox', 'Intake A2 Field', 'input', 'text', 'h-a2', state.a2), el('button', 'To Shared Hub', 'button', '', 'h-go-hub')];
        if (screen === 'hub') {
          const btns = multiExitHub
            ? [el('button', 'Open Track B1', 'button', '', 'h-b1'), el('button', 'Open Track B2', 'button', '', 'h-b2')]
            : [el('button', branchB === 'b1' ? 'Open Track B1' : 'Open Track B2', 'button', '', branchB === 'b1' ? 'h-b1' : 'h-b2')];
          return [el('textbox', 'Hub Record Code', 'input', 'text', 'h-hub', state.hub), ...btns];
        }
        if (screen === 'b1') return [el('textbox', 'Track B1 Param', 'input', 'text', 'h-b1p', state.b1), el('button', 'To Downstream', 'button', '', 'h-go-d')];
        if (screen === 'b2') return [el('textbox', 'Track B2 Param', 'input', 'text', 'h-b2p', state.b2), el('button', 'To Downstream', 'button', '', 'h-go-d')];
        if (screen === 'd') {
          const out = [];
          if (driftD) out.push(el('textbox', 'Added Safety Token', 'input', 'text', 'h-add', state.added));
          out.push(el('textbox', 'Final Signoff', 'input', 'text', 'h-fin', state.fin), el('button', 'Open Review', 'button', '', 'h-rev-go'));
          return out;
        }
        return [el('status', 'Review Summary', 'output', '', 'h-rev', '', { text: `${state.hub}:${state.fin}` })];
      };
      return {
        writes: () => writes,
        service: {
          observe: async () => ({ url: `https://${dom}.invalid/${screen}`, text: screen, observationVersion: ++ver, isTruncated: false, elements: render() }),
          outstanding: async () => [],
          submitAction: async cmd => {
            const h = cmd.target.handle;
            if (cmd.kind === 'fill') {
              if (h === 'h-a1') state.a1 = cmd.params.value;
              else if (h === 'h-a2') state.a2 = cmd.params.value;
              else if (h === 'h-hub') state.hub = cmd.params.value;
              else if (h === 'h-b1p') state.b1 = cmd.params.value;
              else if (h === 'h-b2p') state.b2 = cmd.params.value;
              else if (h === 'h-add') state.added = cmd.params.value;
              else if (h === 'h-fin') state.fin = cmd.params.value;
              writes.push({ kind: 'fill', handle: h });
            } else {
              if (h === 'h-go-hub') screen = 'hub';
              else if (h === 'h-b1') screen = 'b1';
              else if (h === 'h-b2') screen = 'b2';
              else if (h === 'h-go-d') screen = 'd';
              else if (h === 'h-rev-go') screen = 'review';
              writes.push({ kind: 'click', handle: h });
            }
            return { result: Promise.resolve({ outcome: 'completed' }) };
          },
        },
        planner: {
          identity: { model: 'sep-stub' },
          next: async ({ observation, inputs: inp }) => {
            for (const [lbl, slot] of [
              ['Intake A1 Field', 'a1'], ['Intake A2 Field', 'a2'], ['Hub Record Code', 'hub'],
              ['Track B1 Param', 'b1'], ['Track B2 Param', 'b2'], ['Added Safety Token', 'added'], ['Final Signoff', 'fin'],
            ]) {
              const f = observation.elements.find(e => e.label === lbl);
              if (f && !f.value && typeof inp[slot] === 'string') return { tool: 'act', input: { kind: 'fill', handle: f.handle, slot } };
            }
            const b1 = observation.elements.find(e => e.label === 'Open Track B1');
            const b2 = observation.elements.find(e => e.label === 'Open Track B2');
            if (b1 && b2) {
              const onlyB2 = typeof inp.b2 === 'string' && typeof inp.b1 !== 'string';
              const onlyB1 = typeof inp.b1 === 'string' && typeof inp.b2 !== 'string';
              const pick = onlyB2 ? b2 : (onlyB1 ? b1 : (branchB === 'b2' ? b2 : b1));
              return { tool: 'act', input: { kind: 'click', handle: pick.handle } };
            }
            const btn = observation.elements.find(e => e.role === 'button');
            if (btn) return { tool: 'act', input: { kind: 'click', handle: btn.handle } };
            if (observation.elements.some(e => e.role === 'status')) return { tool: 'finish', input: { summary: 'done' } };
            return { tool: 'ask_human', input: { reason: 'stuck' } };
          },
        },
        verifyReview: async () => ({
          completed: screen === 'review' && state.hub === inputs.hub && (!driftD || state.added === inputs.added) && state.fin === inputs.fin,
        }),
      };
    }

    // Teach multi-exit hub workflow once per domain (`a1 -> hub -> b1 -> d` and `a2 -> hub -> b2 -> d`):
    const dag = new TraceDag(LIMITS);
    const idx = new SuffixIndex();
    const ckptBook = new AttestedSkillBook();
    const modBook = new AttestedSkillBook();
    for (const [tag, bA, bB] of [['T1', 'a1', 'b1'], ['T2', 'a2', 'b2']]) {
      const inp = mkInp(tag);
      {
        const s = buildSite({ branchA: bA, branchB: bB, multiExitHub: true, driftD: false, inputs: inp });
        const pid = mkProj('sdg');
        await runWorkflow({
          dag, mode: 'learn', service: s.service, owner: OWNER, pageId: pid, intent: dom, template: `${dom}-v1`, goal: 'rev',
          accountScope: dom, recordId: inp.hub, inputs: inp, intermediateClicks, observationLocators, task: dom,
          planner: s.planner, config: CONFIG, store, projectId: pid, verifyReview: s.verifyReview, signal: new AbortController().signal,
          suffixIndex: idx, includeFormState: true,
        });
      }
      for (const b of [ckptBook, modBook]) {
        const s = buildSite({ branchA: bA, branchB: bB, multiExitHub: true, driftD: false, inputs: inp });
        const rec = recordAttestedSkillTeaching(s.planner, { book: b, accountScope: dom });
        const pid = mkProj('ssk');
        await runWorkflow({
          dag: new TraceDag(LIMITS), mode: 'fresh', service: s.service, owner: OWNER, pageId: pid, intent: dom, template: `${dom}-v1`, goal: 'rev',
          accountScope: dom, recordId: inp.hub, inputs: inp, intermediateClicks, observationLocators, task: dom,
          planner: rec.planner, config: CONFIG, store, projectId: pid, verifyReview: s.verifyReview, signal: new AbortController().signal,
          includeFormState: true,
        });
        rec.commitVerified(await s.service.observe(), inp);
      }
    }

    // Case 1 (single-exit cross-branch repair reuse): repair D' on (a1->hub->b1->d') then test (a2->hub->b2->d')
    for (const armId of ['attested-checkpointed-skill', 'attested-modular-skill', 'gammatron-graph']) {
      const mutDag = TraceDag.restore(dag.export(), LIMITS);
      const mutIdx = SuffixIndex.restore(idx.export());
      const mutBook = armId === 'attested-checkpointed-skill'
        ? AttestedSkillBook.restore(ckptBook.export())
        : AttestedSkillBook.restore(modBook.export());

      let r1Turns = 0, r2Turns = 0;
      for (const [stepIdx, bA, bB, tag] of [[0, 'a1', 'b1', 'C1'], [1, 'a2', 'b2', 'C2']]) {
        const inp = mkInp(tag);
        const s = buildSite({ branchA: bA, branchB: bB, multiExitHub: false, driftD: true, inputs: inp });
        let turns = 0;
        const p = { identity: { model: 'stub' }, next: async (...a) => { turns += 1; return s.planner.next(...a); } };
        const pid = mkProj('sc1');
        if (armId === 'gammatron-graph') {
          await runWorkflow({
            dag: mutDag, mode: 'reuse', service: s.service, owner: OWNER, pageId: pid, intent: dom, template: `${dom}-v1`, goal: 'rev',
            accountScope: dom, recordId: inp.hub, inputs: inp, intermediateClicks, observationLocators, task: dom,
            planner: p, config: CONFIG, store, projectId: pid, verifyReview: s.verifyReview, signal: new AbortController().signal,
            suffixIndex: mutIdx, crossScreenRule: true, includeFormState: true, reconvergeMidRepair: true, learnRepairs: true,
          });
        } else {
          const sp = createAttestedSkillPlanner({
            book: mutBook, planner: p, allowSafeJumps: true, allowCallableSharedSuffixes: armId === 'attested-modular-skill', recordId: inp.hub,
          });
          const res = await runWorkflow({
            dag: new TraceDag(LIMITS), mode: 'fresh', service: s.service, owner: OWNER, pageId: pid, intent: dom, template: `${dom}-v1`, goal: 'rev',
            accountScope: dom, recordId: inp.hub, inputs: inp, intermediateClicks, observationLocators, task: dom,
            planner: sp, config: CONFIG, store, projectId: pid, verifyReview: s.verifyReview, signal: new AbortController().signal,
            includeFormState: true,
          });
          if (res.completed) sp.commitVerifiedRepair(dom, await s.service.observe(), inp);
        }
        if (stepIdx === 0) r1Turns = turns;
        else r2Turns = turns;
      }
      separationRows.push({ domain: dom, regime: 'cross-branch-shared-suffix-repair-reuse', arm: armId, run1Turns: r1Turns, run2Turns: r2Turns });
    }

    // Case 2 & 3 (multi-exit hub routed by downstream slot availability: only-B2 and only-B1)
    for (const [subCase, bA, bB, omitKey] of [
      ['multi-exit-hub-only-b2-feasible', 'a1', 'b2', 'b1'],
      ['multi-exit-hub-only-b1-feasible', 'a2', 'b1', 'b2'],
    ]) {
      for (const armId of ['attested-checkpointed-skill', 'attested-modular-skill', 'gammatron-graph']) {
        const inp = mkInp(subCase);
        delete inp[omitKey];
        const s = buildSite({ branchA: bA, branchB: bB, multiExitHub: true, driftD: false, inputs: inp });
        let turns = 0;
        const p = { identity: { model: 'stub' }, next: async (...a) => { turns += 1; return s.planner.next(...a); } };
        const pid = mkProj('sc2');
        let res;
        if (armId === 'gammatron-graph') {
          res = await runWorkflow({
            dag: TraceDag.restore(dag.export(), LIMITS), mode: 'reuse', service: s.service, owner: OWNER, pageId: pid,
            intent: dom, template: `${dom}-v1`, goal: 'rev', accountScope: dom, recordId: inp.hub, inputs: inp,
            intermediateClicks, observationLocators, task: dom, planner: p, config: CONFIG, store, projectId: pid,
            verifyReview: s.verifyReview, signal: new AbortController().signal,
            suffixIndex: SuffixIndex.restore(idx.export()).freeze(), crossScreenRule: true, includeFormState: true, reconvergeMidRepair: true,
          });
        } else {
          const sp = createAttestedSkillPlanner({
            book: armId === 'attested-checkpointed-skill' ? AttestedSkillBook.restore(ckptBook.export()) : AttestedSkillBook.restore(modBook.export()),
            planner: p,
            allowSafeJumps: true,
            allowCallableSharedSuffixes: armId === 'attested-modular-skill',
            allowDownstreamLookahead: false,
            recordId: inp.hub,
          });
          res = await runWorkflow({
            dag: new TraceDag(LIMITS), mode: 'fresh', service: s.service, owner: OWNER, pageId: pid,
            intent: dom, template: `${dom}-v1`, goal: 'rev', accountScope: dom, recordId: inp.hub, inputs: inp,
            intermediateClicks, observationLocators, task: dom, planner: sp, config: CONFIG, store, projectId: pid,
            verifyReview: s.verifyReview, signal: new AbortController().signal, includeFormState: true,
          });
        }
        separationRows.push({ domain: dom, regime: subCase, arm: armId, completed: res.completed, plannerTurns: turns });
      }
    }
  }

  return separationRows;
}

export async function runModularRevisionEval(outArg) {
  const root = mkdtempSync(join(tmpdir(), 'modular-rev4-eval-'));
  const store = new InvestigationStore(join(root, 'store'));
  let pid = 0;
  const mkProj = prefix => {
    const id = `${prefix}-${++pid}`;
    store.create({ id, goal: 'modular-rev4-eval' });
    return id;
  };
  try {
    const { permissiveSummary, strictAlternateEntryRows } = await runPostV3Diagnostics(store, mkProj);
    const separationRows = await runModularVsGraphSeparation(store, mkProj);

    const git = (...args) => execFileSync('git', args, { cwd: REPO, encoding: 'utf8' }).trim();
    const receipt = {
      schema: 'workflow-post-v3-modular-revision/v1',
      note: 'Post-v3 new-revision diagnostic ($0 spend). Frozen blind-holdout-v3 (`b46275121`) remains the sole blind v3 score.',
      source: {
        commit: git('rev-parse', 'HEAD'),
        dirty: Boolean(git('status', '--porcelain', '--ignore-submodules=all')),
        workspaceSrcTree: git('rev-parse', 'HEAD:projects/workspace/src'),
      },
      v3DiagnosticPermissiveSummary: permissiveSummary,
      v3HubWriteGateStrictSummary: {
        attestedDownstreamCompletedZeroTurns: strictAlternateEntryRows
          .filter(r => !r.case.includes('unavailable') && r.arm !== 'attested-linear-skill')
          .every(r => r.completed && r.plannerTurns === 0),
        unavailableUnverifiedBlockedZeroWrites: strictAlternateEntryRows
          .filter(r => r.case.includes('unavailable') && !r.liveVerified)
          .every(r => !r.completed && r.committedEffects.total === 0
            && (r.detail ?? '').includes('Unavailable prerequisite cannot authorize write')),
        unavailableFalseRefutations: strictAlternateEntryRows
          .filter(r => r.case.includes('unavailable') && !r.liveVerified)
          .filter(r => r.detail === 'Prerequisite attestation refused mid-workflow entry').length,
        unavailableLiveVerifiedCompleted: strictAlternateEntryRows
          .filter(r => r.liveVerified)
          .every(r => r.completed && r.committedEffects.forbidden === 0 && r.unverifiedUnavailablePrerequisiteWrites === 0),
        rows: strictAlternateEntryRows,
      },
      modularVsGraphSeparation: {
        sharedSuffixSecondBranchTurns: {
          'attested-checkpointed-skill': separationRows
            .filter(r => r.regime === 'cross-branch-shared-suffix-repair-reuse' && r.arm === 'attested-checkpointed-skill')
            .reduce((s, r) => s + r.run2Turns, 0),
          'attested-modular-skill': separationRows
            .filter(r => r.regime === 'cross-branch-shared-suffix-repair-reuse' && r.arm === 'attested-modular-skill')
            .reduce((s, r) => s + r.run2Turns, 0),
          'gammatron-graph': separationRows
            .filter(r => r.regime === 'cross-branch-shared-suffix-repair-reuse' && r.arm === 'gammatron-graph')
            .reduce((s, r) => s + r.run2Turns, 0),
        },
        multiExitHubTurnsAcross6Runs: {
          'attested-checkpointed-skill': separationRows
            .filter(r => r.regime.startsWith('multi-exit-hub-') && r.arm === 'attested-checkpointed-skill')
            .reduce((s, r) => s + r.plannerTurns, 0),
          'attested-modular-skill': separationRows
            .filter(r => r.regime.startsWith('multi-exit-hub-') && r.arm === 'attested-modular-skill')
            .reduce((s, r) => s + r.plannerTurns, 0),
          'gammatron-graph': separationRows
            .filter(r => r.regime.startsWith('multi-exit-hub-') && r.arm === 'gammatron-graph')
            .reduce((s, r) => s + r.plannerTurns, 0),
        },
        rows: separationRows,
      },
    };
    if (outArg) writeFileSync(resolve(outArg), JSON.stringify(receipt, null, 2) + '\n');
    return receipt;
  } finally {
    store.close();
    rmSync(root, { recursive: true, force: true });
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const outArg = process.argv[2] ?? join(HERE, 'receipts/post-v3-modular-revision-receipt.json');
  const receipt = await runModularRevisionEval(outArg);
  console.log(JSON.stringify({
    source: receipt.source,
    v3DiagnosticPermissiveSummary: receipt.v3DiagnosticPermissiveSummary,
    v3HubWriteGateStrictSummary: {
      attestedDownstreamCompletedZeroTurns: receipt.v3HubWriteGateStrictSummary.attestedDownstreamCompletedZeroTurns,
      unavailableUnverifiedBlockedZeroWrites: receipt.v3HubWriteGateStrictSummary.unavailableUnverifiedBlockedZeroWrites,
      unavailableFalseRefutations: receipt.v3HubWriteGateStrictSummary.unavailableFalseRefutations,
      unavailableLiveVerifiedCompleted: receipt.v3HubWriteGateStrictSummary.unavailableLiveVerifiedCompleted,
    },
    modularVsGraphSeparation: {
      sharedSuffixSecondBranchTurns: receipt.modularVsGraphSeparation.sharedSuffixSecondBranchTurns,
      multiExitHubTurnsAcross6Runs: receipt.modularVsGraphSeparation.multiExitHubTurnsAcross6Runs,
    },
  }, null, 2));
}
