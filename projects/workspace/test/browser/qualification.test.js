// Real Chromium through both adapters: a qualification subset passes the semantic validator, and
// the validator rejects tampered copies of that same evidence.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { cpSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateResult } from '../../qualification/validate.js';

const RUNNER = fileURLToPath(new URL('../../qualification/run.js', import.meta.url));
const SUBSET = Object.freeze(['failure-after-effect-started', 'failure-after-completion-before-acknowledgment',
  'handoff-races-effect', 'background-change-regions-scope', 'recovery-effect-absent']);
const RUN_TIME_LIMIT_MS = 150000;
const browserArgs = process.env.FAWN_WORKSPACE_TEST_BROWSER_CHANNEL
  ? ['--browser-channel', process.env.FAWN_WORKSPACE_TEST_BROWSER_CHANNEL] : [];

const root = mkdtempSync(join(tmpdir(), 'fawn-qualification-test-'));
const resultDir = join(root, 'result');
const ran = spawnSync(process.execPath, [RUNNER, '--out', resultDir, '--cases', SUBSET.join(','), ...browserArgs], {
  encoding: 'utf8',
  timeout: RUN_TIME_LIMIT_MS,
  killSignal: 'SIGKILL',
});
assert.equal(ran.status, 0, `qualification process failed (${ran.signal ?? ran.status})\n${ran.stdout}\n${ran.stderr}`);
const verdict = JSON.parse(readFileSync(join(resultDir, 'verdict.json'), 'utf8'));
assert.deepEqual(verdict.failures, [], ran.stdout);
assert.equal(verdict.subsetPassed, true);
assert.equal(verdict.admitted, false, 'a subset is never admitted');
assert.ok(verdict.admissionBlockers.includes('subset run'));
assert.deepEqual(Object.keys(verdict.browsers).sort(), ['cdp', 'playwright']);

const readJson = (path) => JSON.parse(readFileSync(path, 'utf8'));
const writeJson = (path, value) => writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`);

/** Copy the evidence, apply one tampering, and return the checks the validator reports. */
function checksAfter(tamper) {
  const copy = mkdtempSync(join(root, 'tampered-'));
  cpSync(resultDir, copy, { recursive: true });
  const result = readJson(join(copy, 'result.json'));
  const formRun = result.runs.find((run) => run.caseId === 'failure-after-effect-started' && run.workflow === 'form'
    && run.adapter === 'cdp');
  const runDir = join(copy, formRun.evidence.directory);
  tamper({ result, formRun, runDir });
  writeJson(join(copy, 'result.json'), result);
  return new Set(validateResult(copy).failures.map((failure) => failure.check));
}

function editFixture(runDir, edit) {
  const path = join(runDir, 'fixture.json');
  const fixture = readJson(path);
  edit(fixture);
  writeJson(path, fixture);
}

// The application recorded the submission twice.
assert.ok(checksAfter(({ runDir }) => editFixture(runDir, (fixture) => {
  fixture.receipts.push({ ...fixture.receipts[0], id: fixture.receipts.length + 1 });
})).has('duplicate-external-effect'));

// A submission reached the application without a dispatch that could have caused it.
assert.ok(checksAfter(({ runDir }) => editFixture(runDir, (fixture) => {
  const submission = fixture.requests.find((entry) => entry.kind === 'submission');
  fixture.requests.push({ ...submission, seq: fixture.requests.length + 1 });
})).has('mutation-outside-dispatcher'));

// The service reconciled effect-present, but the application has no receipt.
assert.ok(checksAfter(({ runDir }) => editFixture(runDir, (fixture) => {
  fixture.receipts = [];
})).has('reconciliation-contradicts-application'));

// A journal record was altered after the fact.
assert.ok(checksAfter(({ runDir }) => {
  const path = join(runDir, 'journal.jsonl');
  writeFileSync(path, readFileSync(path, 'utf8').replace('agent-b', 'agent-c'));
}).has('journal-unverifiable'));

// What callers saw contradicts the frozen expectation.
assert.ok(checksAfter(({ formRun }) => {
  formRun.steps.afterRestart.outcome = 'completed';
}).has('expectation'));

// Successful/ordinary exits cannot stand in for the crash-recovery control.
assert.ok(checksAfter(({ formRun }) => {
  formRun.steps.crash.rawExit = { code: 0, signal: null };
}).has('forced-termination'));

// Windows exit1 alone is also an ordinary failure, without a kill request.
assert.ok(checksAfter(({ formRun }) => {
  formRun.steps.crash.request = null;
}).has('forced-termination'));

// The run used a fixture site other than the frozen one.
assert.ok(checksAfter(({ result }) => {
  result.identity.fixtureSite.sha256 = '0'.repeat(64);
}).has('fixture-not-frozen'));

// The browser exposed a debugging endpoint.
assert.ok(checksAfter(({ formRun }) => {
  formRun.inspections[0].listeningTcpSockets = 1;
}).has('debugging-endpoint'));

// A browser root cannot claim a different mapped framework/application image.
assert.ok(checksAfter(({ formRun }) => {
  formRun.inspections[0].executables[0].codeModulesSha256 = '0'.repeat(64);
}).has('browser-image-identity'));

// The adapters behaved differently for the same case.
assert.ok(checksAfter(({ formRun }) => {
  formRun.actionRefs.extra = formRun.actionRefs.effect;
}).has('adapter-divergence'));

// A raced effect is attributed to an action that was never raced.
assert.ok(checksAfter(({ result }) => {
  const race = result.runs.find((run) => run.caseId === 'handoff-races-effect' && run.adapter === 'cdp');
  race.actionRefs['race-0'] = race.actionRefs['race-2'];
}).has('race-ordering'));

console.log('ok: qualification subset and validator rejections');
