#!/usr/bin/env node
// Release-drift runner (`Release N -> Release N+1`, #88 Item 3):
// Teaches all three primary arms (`attested-linear-skill`, `attested-checkpointed-skill`,
// `gammatron-graph`) on Release N, freezes and SHA-256-pins the taught artifacts, and evaluates
// unchanged on Release N+1 with concurrent record changes, separate-entity approval revocations,
// and lost post-commit responses.
//
// Paid model calls are strictly blocked unless the owner explicitly passes `--approve-paid-model`
// along with explicit `--max-total-usd` and `--max-run-usd` ceilings ($40 / $2 remain proposals).
// Candidate upstream self-hosted release pairs for Stage 2 once authorized:
//   1. Vikunja (Go + SQLite task/project workflow): v0.23.0 -> v0.24.0
//   2. Kanboard (PHP + SQLite board/swimlane task approval): v1.2.37 -> v1.2.40
//   3. BookStack (shelf/page draft review workflow): v24.02 -> v24.05

import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  AttestedSkillBook,
  createAttestedSkillPlanner,
  recordAttestedSkillTeaching,
} from '../../src/client/attested-skill.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { SuffixIndex } from '../../src/client/suffix-eligibility.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { runWorkflow } from '../../src/client/workflow-agent.js';
import { PRIMARY_ARMS } from './fair-fight-score.mjs';

const LIMITS = Object.freeze({ maxNodes: 128, maxEdges: 160, maxSteps: 36 });
const CONFIG = Object.freeze({ maxTurns: 24, maxInputBytes: 60000 });
const sha256 = text => createHash('sha256').update(text, 'utf8').digest('hex');

export function enforcePaidModelGate({ paidModelRequested = false, approvePaidModel = false, maxTotalUsd = null, maxRunUsd = null } = {}) {
  if (!paidModelRequested) return { mode: 'local-zero-dollar', maxTotalUsd: 0, maxRunUsd: 0 };
  if (approvePaidModel !== true) {
    throw Object.assign(
      Error('Paid model calls are blocked: pass --approve-paid-model with owner-approved --max-total-usd and --max-run-usd ($40 total / $2 per run are proposals only).'),
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

/** Cluster-level summary grouped by `(appId, releasePair, workflowId)`, never treating individual turns as independent trials. */
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
        forbiddenEffects: 0,
        duplicateEffects: 0,
        humanRecoveriesRequired: 0,
        plannerTurns: 0,
        predicateReads: 0,
        totalLatencyMs: 0,
        costUsd: 0,
      });
    }
    const c = clusters.get(key);
    c.runs += 1;
    if (row.expectedComplete && row.completed && row.forbiddenEffects === 0 && row.duplicateEffects === 0) {
      c.correctCompletions += 1;
    }
    if (row.expectedComplete && !row.completed) c.falseRefusals += 1;
    c.forbiddenEffects += row.forbiddenEffects;
    c.duplicateEffects += row.duplicateEffects;
    if (row.requiresHumanRecovery) c.humanRecoveriesRequired += 1;
    c.plannerTurns += row.plannerTurns;
    c.predicateReads += row.predicateReads;
    c.totalLatencyMs = Number((c.totalLatencyMs + row.latencyMs).toFixed(2));
    c.costUsd = Number((c.costUsd + (row.costUsd ?? 0)).toFixed(4));
  }
  return [...clusters.values()];
}

/** Freeze Release N artifacts with SHA-256 integrity pins before any Release N+1 run begins. */
export async function freezeReleaseNArtifacts({ appId, releaseN, workflowSpec, outDir }) {
  mkdirSync(outDir, { recursive: true });
  const storeRoot = mkdtempSync(join(tmpdir(), 'rel-n-teach-'));
  const store = new InvestigationStore(storeRoot);
  let seq = 0;
  const artifacts = {};

  try {
    for (const arm of PRIMARY_ARMS) {
      const dag = new TraceDag(LIMITS);
      const index = new SuffixIndex();
      const book = new AttestedSkillBook();
      let teachTurns = 0;
      const t0 = performance.now();

      for (const spec of workflowSpec.teachReleaseN()) {
        const host = spec.build();
        let runTurns = 0;
        const planner = {
          identity: host.planner.identity,
          next: (...a) => { runTurns += 1; return host.planner.next(...a); },
        };
        const isGraph = arm === 'gammatron-graph';
        const rec = !isGraph ? recordAttestedSkillTeaching(planner, { book, accountScope: workflowSpec.accountScope }) : null;
        const pid = `rn-${++seq}`;
        store.create({ id: pid, goal: workflowSpec.goal });
        const res = await runWorkflow({
          dag: isGraph ? dag : new TraceDag(LIMITS),
          mode: 'learn',
          service: host.service,
          owner: {},
          pageId: 'main',
          intent: workflowSpec.intent,
          template: workflowSpec.template,
          goal: workflowSpec.goal,
          accountScope: workflowSpec.accountScope,
          recordId: spec.recordId ?? null,
          inputs: spec.inputs,
          intermediateClicks: workflowSpec.intermediateClicks,
          observationLocators: workflowSpec.observationLocators,
          includeFormState: true,
          learnRepairs: false,
          reconvergeMidRepair: false,
          planner: rec ? rec.planner : planner,
          suffixIndex: isGraph ? index : null,
          task: workflowSpec.goal,
          config: CONFIG,
          store,
          projectId: pid,
          verifyReview: host.verifyReview,
          signal: new AbortController().signal,
        });
        assert.equal(res.completed, true, `Release N teaching failed (${arm}): ${res.detail}`);
        teachTurns += runTurns;
        if (rec) {
          rec.commitVerified(await host.service.observe({ includeFormState: true }), spec.inputs);
        }
      }

      const payload = JSON.stringify({
        appId,
        releaseN,
        workflowId: workflowSpec.id,
        arm,
        teachTurns,
        teachLatencyMs: Number((performance.now() - t0).toFixed(2)),
        graph: arm === 'gammatron-graph' ? dag.export() : null,
        index: arm === 'gammatron-graph' ? index.export() : null,
        book: arm !== 'gammatron-graph' ? book.export() : null,
      }, null, 2);
      const fileName = `frozen-${workflowSpec.id}-${arm}.json`;
      writeFileSync(join(outDir, fileName), payload + '\n');
      artifacts[arm] = { file: fileName, sha256: sha256(payload + '\n') };
    }
  } finally {
    store.close();
    rmSync(storeRoot, { recursive: true, force: true });
  }

  const manifestPath = join(outDir, 'release-n-manifest.json');
  const manifest = { appId, releaseN, workflowId: workflowSpec.id, artifacts };
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  return manifest;
}

/** Evaluate frozen Release N artifacts unchanged on Release N+1 cases (drift + injected faults). */
export async function evaluateReleaseNPlus1({ releaseN1, workflowSpec, manifestDir }) {
  const manifest = JSON.parse(readFileSync(join(manifestDir, 'release-n-manifest.json'), 'utf8'));
  const loaded = {};
  for (const arm of PRIMARY_ARMS) {
    const entry = manifest.artifacts[arm];
    const raw = readFileSync(join(manifestDir, entry.file), 'utf8');
    if (sha256(raw) !== entry.sha256) {
      throw Error(`Frozen Release N artifact checksum mismatch for ${arm}`);
    }
    loaded[arm] = JSON.parse(raw);
  }

  const storeRoot = mkdtempSync(join(tmpdir(), 'rel-n1-eval-'));
  const store = new InvestigationStore(storeRoot);
  let seq = 0;
  const rows = [];

  try {
    for (const testCase of workflowSpec.casesReleaseNPlus1()) {
      for (const arm of PRIMARY_ARMS) {
        const host = testCase.build();
        let plannerTurns = 0;
        let predicateReads = 0;
        const planner = {
          identity: host.planner.identity,
          next: (...a) => { plannerTurns += 1; return host.planner.next(...a); },
        };
        const attestFn = typeof host.attestPrerequisites === 'function'
          ? async (...a) => { predicateReads += 1; return host.attestPrerequisites(...a); }
          : null;
        const isGraph = arm === 'gammatron-graph';
        const skillWrap = !isGraph
          ? createAttestedSkillPlanner({
              book: AttestedSkillBook.restore(loaded[arm].book),
              planner,
              allowSafeJumps: arm === 'attested-checkpointed-skill',
              attestPrerequisites: attestFn,
              recordId: testCase.recordId ?? null,
            })
          : null;
        const pid = `rn1-${++seq}`;
        store.create({ id: pid, goal: workflowSpec.goal });
        const t0 = performance.now();
        const res = await runWorkflow({
          dag: isGraph ? TraceDag.restore(loaded[arm].graph, LIMITS) : new TraceDag(LIMITS),
          mode: isGraph ? 'reuse' : 'fresh',
          service: host.service,
          owner: {},
          pageId: 'main',
          intent: workflowSpec.intent,
          template: workflowSpec.template,
          goal: workflowSpec.goal,
          accountScope: workflowSpec.accountScope,
          recordId: testCase.recordId ?? null,
          inputs: testCase.inputs,
          intermediateClicks: workflowSpec.intermediateClicks,
          observationLocators: workflowSpec.observationLocators,
          includeFormState: true,
          learnRepairs: false,
          reconvergeMidRepair: isGraph,
          planner: skillWrap ?? planner,
          suffixIndex: isGraph ? SuffixIndex.restore(loaded[arm].index).freeze() : null,
          crossScreenRule: isGraph,
          attestPrerequisites: attestFn,
          authorizeStep: host.authorizeStep ?? (async () => {}),
          assertPrerequisite: host.assertPrerequisite
            ? async (...a) => { predicateReads += 1; return host.assertPrerequisite(...a); }
            : null,
          requirePrerequisiteCheck: typeof host.assertPrerequisite === 'function',
          effectForStep: host.effectForStep ?? null,
          task: workflowSpec.goal,
          config: CONFIG,
          store,
          projectId: pid,
          verifyReview: host.verifyReview,
          signal: new AbortController().signal,
        });
        const latencyMs = Number((performance.now() - t0).toFixed(2));
        const writes = host.writes();
        rows.push({
          appId: manifest.appId,
          releasePair: `${manifest.releaseN}->${releaseN1}`,
          workflowId: workflowSpec.id,
          caseId: testCase.id,
          arm,
          expectedComplete: host.expected.complete,
          completed: res.completed === true,
          plannerTurns,
          predicateReads,
          forbiddenEffects: writes.filter(w => w.forbidden).length,
          duplicateEffects: writes.filter(w => w.duplicate).length,
          requiresHumanRecovery: host.expected.complete ? !res.completed : Boolean(testCase.requiresHumanReconcile),
          latencyMs,
          costUsd: 0,
        });
      }
    }
  } finally {
    store.close();
    rmSync(storeRoot, { recursive: true, force: true });
  }

  return {
    releasePair: `${manifest.releaseN}->${releaseN1}`,
    clusters: summarizeByWorkflowReleaseCluster(rows),
    rows,
  };
}

async function runSelfTest() {
  // 1. Verify paid-model gate refuses unapproved calls:
  assert.throws(
    () => enforcePaidModelGate({ paidModelRequested: true, approvePaidModel: false, maxTotalUsd: 40, maxRunUsd: 2 }),
    err => err.code === 'paid-model-not-authorized',
  );

  // 2. Verify Release N freeze -> Release N+1 evaluation + fault accounting ($0):
  const makeReleaseHost = ({ release, inputs, revoked = false }) => {
    let screen = 'edit';
    let obsVer = 0;
    let title = '';
    let note = '';
    const writes = [];
    const el = (role, label, tag, inputType, handle, value, text = '') => ({
      role, label, tag, inputType, handle, selector: '#' + handle,
      digest: `d-${release}-${handle}-${value}-${text}`,
      value, text: text || (tag === 'button' ? label : ''),
      actionability: { visible: true, inert: false, disabled: false },
      formKey: tag === 'input' ? `form-${release}` : null,
      isDefaultValue: value === '',
    });
    return {
      writes: () => writes,
      expected: { complete: !revoked },
      service: {
        async observe() {
          const elements = screen === 'edit'
            ? [
                el('status', 'Approval Banner', 'output', '', 'h-st', '', revoked ? 'Revoked' : 'Approved'),
                ...(release === 'v1.1.0' ? [el('textbox', 'Release Tag', 'input', 'text', 'h-tag', note)] : []),
                el('textbox', 'Task Title', 'input', 'text', 'h-title', title),
                el('button', 'Preview Task', 'button', '', 'h-go'),
              ]
            : [el('status', 'Preview Ready', 'output', '', 'h-prev', '', title)];
          return { url: `https://self-test.invalid/${screen}`, text: screen, observationVersion: ++obsVer, isTruncated: false, elements };
        },
        outstanding: async () => [],
        async submitAction(cmd) {
          if (cmd.kind === 'fill' && cmd.target.handle === 'h-title') title = cmd.params.value;
          else if (cmd.kind === 'fill' && cmd.target.handle === 'h-tag') note = cmd.params.value;
          else if (cmd.kind === 'click') screen = 'preview';
          writes.push({ handle: cmd.target.handle, forbidden: revoked, duplicate: false });
          return { result: Promise.resolve({ outcome: 'completed' }) };
        },
      },
      planner: {
        identity: { model: 'release-self-test-stub' },
        async next({ observation }) {
          if (observation.elements.some(e => e.label === 'Approval Banner' && e.text === 'Revoked')) {
            return { tool: 'ask_human', input: { reason: 'revoked' } };
          }
          const tagEl = observation.elements.find(e => e.label === 'Release Tag');
          if (tagEl && !tagEl.value) return { tool: 'act', input: { kind: 'fill', handle: tagEl.handle, slot: 'releaseTag' } };
          const titleEl = observation.elements.find(e => e.label === 'Task Title');
          if (titleEl && !titleEl.value) return { tool: 'act', input: { kind: 'fill', handle: titleEl.handle, slot: 'title' } };
          const btn = observation.elements.find(e => e.role === 'button');
          if (btn) return { tool: 'act', input: { kind: 'click', handle: btn.handle } };
          return { tool: 'finish', input: { summary: 'ok' } };
        },
      },
      authorizeStep: async () => (revoked ? { ok: false, reason: 'approval-revoked' } : { ok: true }),
      verifyReview: async () => ({ completed: !revoked && screen === 'preview' && title === inputs.title && (release === 'v1.0.0' || note === inputs.releaseTag) }),
    };
  };

  const spec = {
    id: 'board-task-preview',
    intent: 'board:preview',
    template: 'board:v1',
    goal: 'Preview board task',
    accountScope: 'org/alpha',
    intermediateClicks: [['button', 'Preview Task', 'button', '']],
    observationLocators: [
      ['status', 'Approval Banner', 'output', ''],
      ['textbox', 'Release Tag', 'input', 'text'],
      ['textbox', 'Task Title', 'input', 'text'],
      ['button', 'Preview Task', 'button', ''],
      ['status', 'Preview Ready', 'output', ''],
    ],
    teachReleaseN: () => [{
      id: 'teach-v1.0.0',
      recordId: 'TSK-1',
      inputs: { title: 'Audit schema', releaseTag: 'r1' },
      build: () => makeReleaseHost({ release: 'v1.0.0', inputs: { title: 'Audit schema', releaseTag: 'r1' } }),
    }],
    casesReleaseNPlus1: () => [
      {
        id: 'v1.1.0-added-field-drift',
        recordId: 'TSK-2',
        inputs: { title: 'Verify migration', releaseTag: 'r2' },
        build: () => makeReleaseHost({ release: 'v1.1.0', inputs: { title: 'Verify migration', releaseTag: 'r2' } }),
      },
      {
        id: 'v1.1.0-approval-revoked',
        recordId: 'TSK-3',
        inputs: { title: 'Blocked deploy', releaseTag: 'r3' },
        build: () => makeReleaseHost({ release: 'v1.1.0', inputs: { title: 'Blocked deploy', releaseTag: 'r3' }, revoked: true }),
      },
    ],
  };

  const tmp = mkdtempSync(join(tmpdir(), 'rel-drift-selftest-'));
  try {
    await freezeReleaseNArtifacts({ appId: 'selftest-board', releaseN: 'v1.0.0', workflowSpec: spec, outDir: tmp });
    const out = await evaluateReleaseNPlus1({ releaseN1: 'v1.1.0', workflowSpec: spec, manifestDir: tmp });
    assert.equal(out.clusters.length, 3);
    for (const c of out.clusters) {
      assert.equal(c.correctCompletions, 1);
      assert.equal(c.forbiddenEffects, 0);
      assert.equal(c.duplicateEffects, 0);
    }
    console.log('release-drift-runner self-test: ok');
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv.includes('--self-test')) {
    await runSelfTest();
  } else {
    enforcePaidModelGate({
      paidModelRequested: process.argv.includes('--paid-model'),
      approvePaidModel: process.argv.includes('--approve-paid-model'),
      maxTotalUsd: process.argv.includes('--max-total-usd') ? process.argv[process.argv.indexOf('--max-total-usd') + 1] : null,
      maxRunUsd: process.argv.includes('--max-run-usd') ? process.argv[process.argv.indexOf('--max-run-usd') + 1] : null,
    });
    console.log('Usage: release-drift-runner.mjs --self-test (or supply authorized local Release N / N+1 spec)');
  }
}
