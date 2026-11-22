#!/usr/bin/env node
// Scores an independent holdout (see holdout-interface.md) against the frozen arms. The cases are
// loaded as written; this file never edits them. It refuses to run if the holdout's files do not
// match their SHA256SUMS, and it records the source revision it ran against.
//
//   node holdout-score.mjs HOLDOUT_DIR OUT.json
//
// Arms: exact matching; the repaired index and profile matchers (controls); the cross-screen rule
// (candidate, the only arm given the host's attestation); and the recovery-capable skill.
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { InvestigationStore } from '../../src/client/investigation.js';
import { SuffixIndex } from '../../src/client/suffix-eligibility.js';
import { skillPlanner, skillRecorder } from '../../src/client/skill-exec.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { runWorkflow } from '../../src/client/workflow-agent.js';

const [holdoutArg, outArg] = process.argv.slice(2);
if (!holdoutArg || !outArg) throw Error('usage: holdout-score.mjs HOLDOUT_DIR OUT.json');
const holdout = resolve(holdoutArg);
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const pinned = readFileSync(join(holdout, 'SHA256SUMS'), 'utf8').trim().split('\n').map(line => line.trim().split(/\s+/));
for (const [hash, file] of pinned) {
  if (sha(readFileSync(join(holdout, file.replace(/^\*/, '')))) !== hash) throw Error(`Holdout file does not match its pin: ${file}`);
}
const { workflows } = await import(pathToFileURL(join(holdout, 'cases.mjs')).href);

const LIMITS = Object.freeze({ maxNodes: 96, maxEdges: 96, maxSteps: 32 });
const CONFIG = Object.freeze({ maxTurns: 24, maxInputBytes: 60000 });
const ARMS = Object.freeze({
  exact: { matcher: null },
  index: { matcher: 'index' },
  profile: { matcher: 'profile' },
  cross: { matcher: 'index', cross: true },
  skill: { skill: true },
});
const SUFFIX_PHASES = new Set(['certified-suffix-replay', 'suffix-eligible-replay']);
const root = mkdtempSync(join(tmpdir(), 'holdout-score-'));
const store = new InvestigationStore(root);
let sequence = 0;

/** Count the turns the case's own planner stub takes, whatever wraps it. */
function counted(planner) {
  const state = { turns: 0 };
  return { state, planner: { identity: planner.identity, next: async (...args) => { state.turns += 1; return planner.next(...args); } } };
}
function options(workflow, host, inputs, extra) {
  const projectId = `holdout-${++sequence}`;
  store.create({ id: projectId, goal: workflow.goal });
  return { service: host.service, owner: {}, pageId: 'main', intent: workflow.intent, template: workflow.template, goal: workflow.goal,
    accountScope: workflow.accountScope, inputs, intermediateClicks: workflow.intermediateClicks,
    observationLocators: workflow.observationLocators, learnRepairs: false,
    assertContext: host.assertContext ?? (async () => {}), authorizeStep: host.authorizeStep ?? (async () => {}),
    assertPrerequisite: host.assertPrerequisite ?? null, requirePrerequisiteCheck: typeof host.assertPrerequisite === 'function',
    task: workflow.goal, config: CONFIG, store, projectId, verifyReview: host.verifyReview, signal: new AbortController().signal, ...extra };
}

const rows = [], teaching = [];
try {
  for (const workflow of workflows) {
    // Teach each arm from a fresh copy of the same taught host with the same planner stub.
    const taught = {};
    for (const [armId, arm] of Object.entries(ARMS)) {
      const host = workflow.teach();
      const dag = new TraceDag(LIMITS), index = arm.matcher === 'index' ? new SuffixIndex() : null;
      const recorder = arm.skill ? skillRecorder(host.planner) : null;
      const result = await runWorkflow({ ...options(workflow, host, workflow.inputs.teach, {
        dag, mode: 'learn', reconvergeMidRepair: false, planner: recorder?.planner ?? host.planner,
        suffixIndex: index, suffixEligibility: arm.matcher === 'profile' }) });
      teaching.push({ workflow: workflow.id, arm: armId, completed: result.completed, detail: result.detail });
      if (!result.completed) throw Error(`Teaching failed for ${workflow.id} / ${armId}: ${result.detail}`);
      taught[armId] = { graph: dag.export(), index: index?.export() ?? null, skill: recorder?.skill() ?? null };
    }
    for (const testCase of workflow.cases) {
      for (const [armId, arm] of Object.entries(ARMS)) {
        const host = testCase.build();
        const stub = counted(host.planner);
        const skillRun = arm.skill ? skillPlanner({ skill: taught[armId].skill, planner: stub.planner }) : null;
        let result, error = null;
        try {
          result = await runWorkflow({ ...options(workflow, host, workflow.inputs.run, {
            dag: TraceDag.restore(taught[armId].graph, LIMITS), mode: arm.skill ? 'fresh' : 'reuse', reconvergeMidRepair: !arm.skill,
            planner: skillRun ?? stub.planner,
            suffixIndex: arm.matcher === 'index' ? SuffixIndex.restore(taught[armId].index).freeze() : null,
            suffixEligibility: arm.matcher === 'profile',
            ...(arm.cross ? { crossScreenRule: true, attestPrerequisites: host.attestPrerequisites ?? null } : {}) }) });
        } catch (failure) { error = failure.message; result = { completed: false, detail: failure.message }; }
        const events = result.traceEvents ?? [];
        const replayed = events.filter(event => SUFFIX_PHASES.has(event.phase)
          || event.acceptedWhy === 'suffix-eligible-footprint-and-dirty-form-guards-verified').length;
        const certifications = arm.matcher === 'index' ? (result.suffix?.certified ?? 0)
          : arm.matcher === 'profile' ? (result.certifiedSuffixRejoins?.length ?? 0) : 0;
        const writes = host.writes();
        rows.push({ workflow: workflow.id, case: testCase.id, kind: testCase.kind, pairId: testCase.pairId ?? null,
          hostHasWriteCheck: Boolean(testCase.hostHasWriteCheck), arm: armId,
          completed: result.completed === true, expectedComplete: host.expected.complete === true,
          allowedWrites: host.expected.allowedWrites, plannerTurns: stub.state.turns, cachedSteps: result.cacheSteps ?? 0,
          certified: certifications > 0 || replayed > 0, certifications, suffixReplayedSteps: replayed,
          attestedCertifications: result.suffix?.attested ?? 0, skill: skillRun?.stats() ?? null,
          writes: writes.length, writeHandles: writes.map(write => write.handle), detail: result.detail ?? null, error });
      }
    }
  }
} finally {
  store.close();
  rmSync(root, { recursive: true, force: true });
}

// ----------------------------------------------------------------------------------- counting
const key = row => `${row.workflow}/${row.case}`;
const byCase = new Map();
for (const row of rows) byCase.set(key(row), { ...(byCase.get(key(row)) ?? {}), [row.arm]: row });
const matcherArms = ['index', 'profile', 'cross'];
const useful = (row, exact) => row.completed && row.certified && row.plannerTurns < exact.plannerTurns;
const summary = {};
for (const armId of Object.keys(ARMS)) {
  const mine = rows.filter(row => row.arm === armId);
  const must = mine.filter(row => row.kind === 'must-complete'), mustNot = mine.filter(row => row.kind === 'must-not-proceed');
  const exactOf = row => byCase.get(key(row)).exact;
  summary[armId] = {
    mustComplete: must.length,
    completed: must.filter(row => row.completed).length,
    plannerTurnsOnMustComplete: must.reduce((sum, row) => sum + row.plannerTurns, 0),
    usefulRejoins: must.filter(row => useful(row, exactOf(row))).length,
    restingOnAttestation: must.filter(row => useful(row, exactOf(row)) && row.attestedCertifications > 0).length,
    falseRefusals: matcherArms.includes(armId) ? must.filter(row => !useful(row, exactOf(row))
      && matcherArms.some(other => other !== armId && useful(byCase.get(key(row))[other], exactOf(row)))).length : null,
    fewerTurnsThanExact: must.filter(row => row.completed && row.plannerTurns < exactOf(row).plannerTurns).length,
    mustNotProceed: mustNot.length,
    stopped: mustNot.filter(row => !row.completed).length,
    completedWhereForbidden: mustNot.filter(row => row.completed).length,
    unsafeCertifications: mustNot.filter(row => row.certified).length,
    writesWhereNoneAllowed: mustNot.filter(row => row.allowedWrites === 'none').reduce((sum, row) => sum + row.writes, 0),
    writesBeyondExact: mine.reduce((sum, row) => sum + Math.max(0, row.writes - exactOf(row).writes), 0),
    unsafeWhereHostHasNoCheck: mustNot.filter(row => !row.hostHasWriteCheck && row.certified).length,
  };
}
const repo = resolve(dirname(fileURLToPath(import.meta.url)), '../../../..');
const git = (...args) => execFileSync('git', args, { cwd: repo, encoding: 'utf8' }).trim();
const receipt = {
  schema: 'workflow-holdout-score/v1',
  note: 'Scripted planner stub from the holdout itself. No model was called.',
  source: { commit: git('rev-parse', 'HEAD'), dirty: Boolean(git('status', '--porcelain', '--ignore-submodules=all')),
    workspaceSrcTree: git('rev-parse', 'HEAD:projects/workspace/src') },
  holdout: { files: Object.fromEntries(pinned.map(([hash, file]) => [file, hash])), workflows: workflows.length,
    cases: workflows.reduce((sum, workflow) => sum + workflow.cases.length, 0) },
  teaching, summary, rows,
};
writeFileSync(resolve(outArg), JSON.stringify(receipt, null, 1) + '\n');
console.log(JSON.stringify({ source: receipt.source, holdout: receipt.holdout, summary }, null, 1));
