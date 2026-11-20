#!/usr/bin/env node
// Fawn workspace qualification — semantic evidence validator.
//
// Admits a qualification result only when real run evidence satisfies the frozen case set:
// - identities: the frozen case set, fixture site and oracles; optionally the current source
// - every journal re-verified (hash chain) and replayed, with ordering invariants checked
// - expectations compared against three independent sources: what callers saw (steps), the
//   replayed journal, and the fixture site's own request log and receipts
// - external effects reconciled with the fixture's receipts, never with service records alone
// - identical behaviour across adapters, and contract requirement coverage
//
// Usage: node qualification/validate.js <resultDir> [--require-current-source]

import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readVerifiedJournal } from '../src/journal.js';
import { ACTION_STATUS, OUTCOMES, RECORD_TYPES, applyRecord, createState, describeAction } from '../src/state.js';
import { formEffectKey } from '../src/workflows/form-submission.js';
import { REPO_ROOT, executableIdentityKey, repoFileSha256, treeDigest } from './identity.js';
import { summarizeAction } from './summaries.js';
import { terminationMatches } from './termination.js';
import { evidencePath, caseSetMatches } from './evidence-input.js';
import { profileFailures } from './browser-profile.js';

const CASE_SET_PATH = 'projects/workspace/config/fawn-workspace-qualification.json';
const STRATEGY_PATH = 'projects/workspace/config/doe-product-strategy.json';
const VERDICT_SCHEMA_VERSION = 1;
const VALIDATOR_PATH = 'projects/workspace/qualification/validate.js';
const NO_WORKFLOW = 'none';
const DISPATCHED_RACE_CLASSES = Object.freeze(['in-flight-at-handoff', 'settled-before-handoff']);
const CURRENT_IDENTITIES = Object.freeze({
  serviceSource: () => treeDigest('projects/workspace/src').sha256,
  runtimeSelector: () => repoFileSha256('browser/chromium/scripts/browser-runtime-selector.mjs'),
  harness: () => treeDigest('projects/workspace/qualification').sha256,
  serviceConfig: () => repoFileSha256('projects/workspace/config/fawn-workspace-service.json'),
  packageLock: () => repoFileSha256('projects/workspace/package-lock.json'),
});

function loadJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

function canonical(value) {
  return JSON.stringify(value, (key, nested) => (nested && typeof nested === 'object' && !Array.isArray(nested)
    ? Object.fromEntries(Object.entries(nested).sort(([a], [b]) => (a < b ? -1 : 1)))
    : nested));
}

/** Merge a case's shared expectation with its per-workflow additions. */
function mergeExpected(base, extra) {
  if (extra === undefined) return base;
  if (Array.isArray(extra) || extra === null || typeof extra !== 'object') return extra;
  const merged = { ...(base ?? {}) };
  for (const [key, value] of Object.entries(extra)) merged[key] = mergeExpected(merged[key], value);
  return merged;
}

/** Every expected key must match; arrays and primitives match exactly. */
function matchPartial(expected, observed, path, mismatches, oracles) {
  if (Array.isArray(expected) || expected === null || typeof expected !== 'object') {
    if (canonical(expected) !== canonical(observed)) {
      mismatches.push(`${path}: expected ${canonical(expected)}, observed ${canonical(observed)}`);
    }
    return;
  }
  if (observed === null || typeof observed !== 'object') {
    mismatches.push(`${path}: expected object, observed ${canonical(observed)}`);
    return;
  }
  for (const [key, value] of Object.entries(expected)) {
    if (key === 'artifact') {
      const sha256 = oracles.reportSha256[value];
      if (observed.artifactSha256 !== sha256) {
        mismatches.push(`${path}.artifact: expected ${value} (${sha256}), observed ${observed.artifactSha256}`);
      }
    } else {
      matchPartial(value, observed[key], `${path}.${key}`, mismatches, oracles);
    }
  }
}

function unsettled(action) {
  return action.status === ACTION_STATUS.QUEUED || (action.status === ACTION_STATUS.DISPATCHED && !action.outcome);
}

/**
 * Re-verify and replay a journal, checking ordering invariants record by record.
 */
function deriveJournal(path) {
  const { records } = readVerifiedJournal(path);
  const state = createState();
  const violations = [];
  if (records[0]?.type !== RECORD_TYPES.SERVICE_RESTORED) violations.push('journal does not begin with service restoration');
  for (const record of records) {
    const { body } = record;
    const workspace = state.workspaces.get(body.workspaceId);
    if (record.type === RECORD_TYPES.SERVICE_RESTORED) {
      for (const candidate of state.workspaces.values()) {
        for (const action of candidate.actions.values()) {
          if (unsettled(action)) violations.push(`seq ${record.seq}: restored with unsettled ${action.request.actionId}`);
        }
      }
    }
    if (record.type === RECORD_TYPES.ACTION_ADMITTED && body.ownerGeneration !== workspace?.ownerGeneration) {
      violations.push(`seq ${record.seq}: ${body.actionId} admitted under generation ${body.ownerGeneration}`);
    }
    if (record.type === RECORD_TYPES.ACTION_DISPATCH_STARTED) {
      const action = workspace?.actions.get(body.actionId);
      if (body.ownerGeneration !== workspace?.ownerGeneration || action?.request.ownerGeneration !== workspace?.ownerGeneration) {
        violations.push(`seq ${record.seq}: ${body.actionId} dispatched after its generation advanced`);
      }
    }
    if (record.type === RECORD_TYPES.ACTION_OUTCOME && body.boundary?.isAtomic !== false) {
      violations.push(`seq ${record.seq}: outcome without the non-atomic boundary`);
    }
    try {
      applyRecord(state, record);
    } catch (error) {
      violations.push(error.message);
    }
  }
  const workspace = [...state.workspaces.values()][0] ?? null;
  return {
    records,
    workspace,
    violations,
    commandRejections: records.filter((record) => record.type === RECORD_TYPES.COMMAND_REJECTED).map((record) => record.body.code),
    pageChangeObservations: records.filter((record) => record.type === RECORD_TYPES.OBSERVATION_RECORDED
      && record.body.reason === 'page-change').length,
  };
}

function journalAction(journal, actionId) {
  const action = journal.workspace?.actions.get(actionId);
  if (!action) return null;
  return { ...summarizeAction(describeAction(action)), observationScope: action.dispatch?.observationScope?.kind ?? null };
}

function dispatchedActions(journal, predicate) {
  return [...(journal.workspace?.actions.values() ?? [])]
    .filter((action) => action.status === ACTION_STATUS.DISPATCHED && predicate(action));
}

function matchesRequest(entry, request) {
  return entry.server === request.server && entry.method === request.method && entry.path === request.path;
}

function oracleCounts(fixture, wf) {
  const { requests } = fixture;
  const downloads = {};
  for (const entry of requests.filter((candidate) => candidate.kind === 'download')) {
    downloads[entry.path] = (downloads[entry.path] ?? 0) + 1;
  }
  return {
    effectRequests: wf ? requests.filter((entry) => matchesRequest(entry, wf.effectRequest)).length : 0,
    receipts: fixture.receipts.filter((receipt) => !receipt.seeded).length,
    foreignRequests: requests.filter((entry) => entry.server === 'foreign').length,
    markerRequests: requests.filter((entry) => entry.path.startsWith('/marker/')).length,
    applicationDeduplicated: requests.filter((entry) => entry.kind === 'submission' && entry.duplicateOf).length,
    requests: requests.length,
    downloads,
  };
}

function nonEmptyFields(fields) {
  return Object.fromEntries(Object.entries(fields).filter(([key, value]) => value !== '' && key !== 'idempotencyKey'));
}

/**
 * External effects judged by the application's receipts: no duplicates, and every submit
 * action's state consistent with whether its effect exists.
 */
function checkExternalEffects(journal, fixture, caseSet, fail) {
  const formUrl = `${fixture.origin}${caseSet.workflows.form.task.formPath}`;
  const receiptKeys = fixture.receipts.map((receipt) => formEffectKey(formUrl, nonEmptyFields(receipt.fields)));
  const people = fixture.receipts.map((receipt) => `${receipt.fields.name}\u0000${receipt.fields.email}`);
  if (new Set(people).size !== people.length) fail('duplicate-external-effect', 'the application recorded one submission twice');
  if (new Set(receiptKeys).size !== receiptKeys.length) fail('duplicate-external-effect', 'two receipts share an effect key');
  const atBySeq = new Map(journal.records.map((record) => [record.seq, record.at]));
  const receiptTimes = fixture.receipts.map((receipt, index) => ({ key: receiptKeys[index], at: Date.parse(receipt.receivedAt) }));
  const submits = [...(journal.workspace?.actions.values() ?? [])].filter((action) => action.request.kind === 'submit');
  const byKey = new Map();
  for (const action of submits) {
    const key = action.request.effect?.effectKey;
    if (!byKey.has(key)) byKey.set(key, []);
    byKey.get(key).push(action);
  }
  for (const [key, actions] of byKey) {
    const receipts = receiptKeys.filter((candidate) => candidate === key).length;
    const outcomes = actions.map((action) => action.outcome?.outcome ?? null);
    if (outcomes.includes(OUTCOMES.COMPLETED) && receipts !== 1) {
      fail('completed-without-effect', `${key}: completed submit, ${receipts} receipts`);
    }
    if (actions.every((action) => action.status === ACTION_STATUS.NEVER_DISPATCHED) && receipts !== 0) {
      fail('undispatched-with-effect', `${key}: never dispatched, ${receipts} receipts`);
    }
    if (outcomes.every((outcome) => outcome === OUTCOMES.FAILED) && receipts !== 0) {
      fail('failed-with-effect', `${key}: failed submit, ${receipts} receipts`);
    }
    // A reconciliation is judged against the receipts that existed when it was recorded; a
    // later explicit resubmission may legitimately create the effect afterwards.
    for (const action of actions) {
      for (const reconciliation of action.reconciliations) {
        const recordedAt = Date.parse(atBySeq.get(reconciliation.seq));
        const existing = receiptTimes.filter((entry) => entry.key === key && entry.at <= recordedAt).length;
        if (reconciliation.result === 'effect-present' && existing === 0) {
          fail('reconciliation-contradicts-application', `${key}: effect-present, no receipt by then`);
        }
        if (reconciliation.result === 'effect-absent' && existing !== 0) {
          fail('reconciliation-contradicts-application', `${key}: effect-absent, receipt already existed`);
        }
      }
    }
  }
}

/** Effects the application observed must not outnumber the dispatches that could cause them. */
function checkDispatcherCoverage(journal, fixture, wf, fail) {
  const counts = oracleCounts(fixture, wf);
  if (counts.foreignRequests !== 0) fail('foreign-origin-reached', `${counts.foreignRequests} requests to an ungranted origin`);
  const submissions = fixture.requests.filter((entry) => entry.kind === 'submission').length;
  const dispatchedSubmits = dispatchedActions(journal, (action) => action.request.kind === 'submit').length;
  if (submissions > dispatchedSubmits) fail('mutation-outside-dispatcher', `${submissions} submissions, ${dispatchedSubmits} dispatched submits`);
  const downloads = fixture.requests.filter((entry) => entry.kind === 'download').length;
  const dispatchedDownloads = dispatchedActions(journal, (action) => action.request.kind === 'download').length;
  if (downloads > dispatchedDownloads) fail('mutation-outside-dispatcher', `${downloads} downloads, ${dispatchedDownloads} dispatched downloads`);
  if (wf) {
    const effects = dispatchedActions(journal, (action) => action.request.actionId.endsWith(wf.effectActionSuffix)).length;
    if (counts.effectRequests > effects) fail('mutation-outside-dispatcher', `${counts.effectRequests} effect requests, ${effects} dispatched`);
  }
  if (counts.markerRequests > 0) {
    const markers = dispatchedActions(journal, (action) => action.request.target?.url?.includes('/marker/')).length;
    if (counts.markerRequests > markers) fail('mutation-outside-dispatcher', `${counts.markerRequests} marker requests, ${markers} dispatched`);
  }
}

function checkArtifacts(journal, fixture, caseSet, fail) {
  const frozen = Object.values(caseSet.oracles.reportSha256);
  if (canonical(fixture.reportSha256) !== canonical(caseSet.oracles.reportSha256)) {
    fail('oracle-mismatch', 'fixture report bytes differ from the frozen oracle');
  }
  const served = new Set(fixture.requests.filter((entry) => entry.kind === 'download').map((entry) => entry.sha256));
  for (const action of dispatchedActions(journal, (candidate) => candidate.request.kind === 'download')) {
    if (action.outcome?.outcome !== OUTCOMES.COMPLETED) continue;
    const sha256 = action.outcome.evidence?.effect?.sha256;
    if (!frozen.includes(sha256) || !served.has(sha256)) {
      fail('artifact-not-served', `${action.request.actionId}: saved ${sha256} was not served by the application`);
    }
  }
}

/** Classify each raced effect from journal order alone. */
function classifyRace(journal, actionId, step) {
  const action = journal.workspace?.actions.get(actionId);
  if (!action) {
    const rejected = journal.records.find((record) => record.type === RECORD_TYPES.COMMAND_REJECTED && record.body.actionId === actionId);
    if (!rejected) return step?.effectReached ? 'unrecorded' : 'not-reached';
    return rejected.body.code === 'stale-owner-generation' ? 'rejected-at-admission' : `rejected-${rejected.body.code}`;
  }
  if (action.status === ACTION_STATUS.NEVER_DISPATCHED) {
    if (action.notDispatched.stage === 'handoff') return 'ended-at-handoff';
    if (action.notDispatched.stage === 'dispatch' && action.notDispatched.code === 'stale-owner-generation') return 'rejected-at-dispatch';
    return `never-dispatched-${action.notDispatched.code}`;
  }
  const handoff = journal.records.find((record) => record.type === RECORD_TYPES.OWNERSHIP_ADVANCED
    && record.body.previous?.ownerGeneration === action.request.ownerGeneration);
  if (!handoff) return 'no-handoff';
  if (action.dispatch.seq > handoff.seq) return 'dispatched-after-handoff';
  return action.outcome && action.outcome.seq < handoff.seq ? 'settled-before-handoff' : 'in-flight-at-handoff';
}

function checkRace(run, caseSpec, wf, journal, fixture, fail) {
  const steps = run.steps.race ?? [];
  const classes = [];
  caseSpec.race.iterations.forEach((iteration, index) => {
    const actionId = run.actionRefs[`race-${index}`];
    const cls = classifyRace(journal, actionId, steps[index]);
    classes.push(cls);
    if (!caseSpec.race.allowedClasses.includes(cls)) fail('race-ordering', `iteration ${index} (${iteration.order}): ${cls}`);
    if (iteration.expectedClass && cls !== iteration.expectedClass) {
      fail('race-ordering', `iteration ${index} (${iteration.order}): expected ${iteration.expectedClass}, observed ${cls}`);
    }
    if (cls === 'in-flight-at-handoff') {
      const disclosed = steps[index]?.handoffDisclosed;
      if (disclosed?.dispatchStatus !== ACTION_STATUS.DISPATCHED || disclosed.outcome !== null) {
        fail('in-flight-not-disclosed', `iteration ${index}: handoff disclosed ${canonical(disclosed)}`);
      }
    }
  });
  const dispatched = classes.filter((cls) => DISPATCHED_RACE_CLASSES.includes(cls)).length;
  const effects = oracleCounts(fixture, wf).effectRequests;
  if (effects !== dispatched) fail('race-effects', `${effects} effect requests for ${dispatched} dispatched raced effects`);
  return classes;
}

function checkAuthorityUnavailable(runDir, run, fail, platform) {
  if (!run.evidence.corruptJournal) return fail('evidence-missing', 'corrupt journal copy');
  try {
    readVerifiedJournal(evidencePath(runDir, run.evidence.corruptJournal, platform));
    fail('corruption-undetected', 'the corrupted journal verified');
  } catch (error) {
    if (error.code !== 'journal-corrupt') fail('corruption-undetected', error.message);
  }
}

function validateRun({ resultDir, run, caseSpec, caseSet, failures, platform }) {
  const fail = (check, detail) => failures.push({ caseId: run.caseId, workflow: run.workflow, adapter: run.adapter, check, detail });
  const wf = caseSet.workflows[run.workflow] ?? null;
  const runDir = evidencePath(resultDir, run.evidence.directory, platform);
  if (run.error) fail('run-error', run.error.message);
  const fixture = loadJson(evidencePath(runDir, run.evidence.fixture, platform));
  let journal;
  try {
    journal = deriveJournal(evidencePath(runDir, run.evidence.journal, platform));
  } catch (error) {
    fail('journal-unverifiable', error.message);
    return null;
  }
  for (const violation of journal.violations) fail('journal-invariant', violation);
  const expected = mergeExpected(caseSpec.expected, caseSpec.expectedByWorkflow?.[run.workflow]);
  if (expected.steps?.crash && !terminationMatches(run.steps.crash, platform)) {
    fail('forced-termination', `kill request and raw OS exit do not establish abrupt termination on ${platform}`);
  }
  const mismatches = [];
  if (expected.steps) matchPartial(expected.steps, run.steps, 'steps', mismatches, caseSet.oracles);
  const actions = Object.fromEntries(Object.entries(run.actionRefs).map(([ref, actionId]) => [ref, journalAction(journal, actionId)]));
  if (expected.actions) matchPartial(expected.actions, actions, 'actions', mismatches, caseSet.oracles);
  if (expected.commandRejections) matchPartial(expected.commandRejections, journal.commandRejections, 'commandRejections', mismatches, caseSet.oracles);
  if (expected.oracle) {
    const counts = oracleCounts(fixture, wf);
    const { downloads, ...scalars } = expected.oracle;
    matchPartial(scalars, counts, 'oracle', mismatches, caseSet.oracles);
    for (const [path, count] of Object.entries(downloads ?? {})) {
      if ((counts.downloads[path] ?? 0) !== count) mismatches.push(`oracle.downloads.${path}: expected ${count}, observed ${counts.downloads[path] ?? 0}`);
    }
  }
  if (expected.journal?.minPageChangeObservations !== undefined
    && journal.pageChangeObservations < expected.journal.minPageChangeObservations) {
    mismatches.push(`journal.pageChangeObservations: expected at least ${expected.journal.minPageChangeObservations}, observed ${journal.pageChangeObservations}`);
  }
  for (const mismatch of mismatches) fail('expectation', mismatch);
  checkDispatcherCoverage(journal, fixture, wf, fail);
  checkExternalEffects(journal, fixture, caseSet, fail);
  checkArtifacts(journal, fixture, caseSet, fail);
  for (const inspection of run.inspections) {
    const modulesHash = createHash('sha256').update(canonical(inspection.codeModules ?? [])).digest('hex');
    if (!Array.isArray(inspection.codeModules)
        || inspection.executables.some((image) => image.codeModulesSha256 !== modulesHash)) {
      fail('browser-image-identity', 'mapped browser code modules do not match the recorded root identity');
    }
    if (inspection.listeningTcpSockets !== 0) fail('debugging-endpoint', `${inspection.listeningTcpSockets} listening TCP sockets`);
    if (inspection.devToolsActivePortFiles !== 0) fail('debugging-endpoint', 'DevToolsActivePort file in the profile');
  }
  const raceClasses = caseSpec.race ? checkRace(run, caseSpec, wf, journal, fixture, fail) : null;
  if (caseSpec.procedure === 'authority-unavailable') checkAuthorityUnavailable(runDir, run, fail, platform);
  const deterministicRace = raceClasses?.filter((_, index) => caseSpec.race.iterations[index].expectedClass);
  return caseSpec.race
    ? { raceClasses: deterministicRace }
    : { actions, commandRejections: journal.commandRejections };
}

function plannedKeys(caseSet, adapters) {
  return caseSet.cases.flatMap((caseSpec) => caseSpec.workflows.flatMap((workflow) => adapters.map((adapter) => `${caseSpec.id}|${workflow}|${adapter}`)));
}

function requirementCoverage(caseSet, strategy, failedCases) {
  const required = strategy.fawnWorkspace.steps.flatMap((step) => step.requiredEvidence.map((id) => ({ id, step: step.id })));
  const known = new Set(required.map((entry) => entry.id));
  const unknown = caseSet.cases.flatMap((caseSpec) => caseSpec.requirements.filter((id) => !known.has(id))
    .map((id) => ({ caseId: caseSpec.id, id })));
  const requirements = required.map(({ id, step }) => {
    const cases = caseSet.cases.filter((caseSpec) => caseSpec.requirements.includes(id)).map((caseSpec) => caseSpec.id);
    const status = cases.length === 0 ? 'not-covered' : (cases.some((caseId) => failedCases.has(caseId)) ? 'failed' : 'established');
    return { id, step, status, cases };
  });
  return { requirements, unknown };
}

function browserIdentities(runs, fail) {
  const byAdapter = {};
  for (const run of runs) {
    for (const inspection of run.inspections) {
      for (const executable of inspection.executables) {
        byAdapter[run.adapter] ??= new Map();
        byAdapter[run.adapter].set(executableIdentityKey(executable), executable);
      }
    }
  }
  const adapters = [...new Set(runs.map((run) => run.adapter))];
  for (const adapter of adapters) {
    const count = byAdapter[adapter]?.size ?? 0;
    if (count !== 1) fail({ adapter, check: 'browser-identity', detail: `${count} distinct browser executables` });
  }
  return Object.fromEntries(Object.entries(byAdapter).map(([adapter, executables]) => [adapter, [...executables.values()]]));
}

/**
 * Validate a result directory written by run.js.
 */
function validateResult(resultDir, { requireCurrentSource = false } = {}) {
  const result = loadJson(join(resultDir, 'result.json'));
  const caseSet = loadJson(join(REPO_ROOT, CASE_SET_PATH));
  const strategy = loadJson(join(REPO_ROOT, STRATEGY_PATH));
  const failures = [];
  const fail = (failure) => failures.push(failure);
  for (const detail of profileFailures(resultDir, result)) fail({ check: 'browser-build-profile', detail });
  if (result.caseSetVersion !== caseSet.caseSetVersion
      || !caseSetMatches(resultDir, result.identity.caseSet.sha256, readFileSync(join(REPO_ROOT, CASE_SET_PATH)))) {
    fail({ check: 'case-set-identity', detail: 'the result ran a different case set than the frozen one' });
  }
  if (result.identity.fixtureSite.sha256 !== caseSet.harness.fixtureSite.sha256) {
    fail({ check: 'fixture-not-frozen', detail: `fixture site ${result.identity.fixtureSite.sha256} is not the frozen ${caseSet.harness.fixtureSite.sha256}` });
  }
  if (requireCurrentSource) {
    for (const [name, current] of Object.entries(CURRENT_IDENTITIES)) {
      const recorded = result.identity[name]?.sha256;
      if (recorded !== current()) fail({ check: 'source-identity', detail: `${name} ${recorded} differs from the current tree` });
    }
  }
  const casesById = new Map(caseSet.cases.map((caseSpec) => [caseSpec.id, caseSpec]));
  const signatures = new Map();
  const failedCases = new Set();
  for (const run of result.runs) {
    const caseSpec = casesById.get(run.caseId);
    if (!caseSpec || !caseSpec.workflows.includes(run.workflow)) {
      fail({ caseId: run.caseId, check: 'unplanned-run', detail: `${run.workflow} ${run.adapter}` });
      continue;
    }
    const before = failures.length;
    const signature = validateRun({ resultDir, run, caseSpec, caseSet, failures, platform: result.identity.os.platform });
    if (failures.length > before) failedCases.add(run.caseId);
    const group = `${run.caseId}|${run.workflow}`;
    if (!signatures.has(group)) signatures.set(group, []);
    signatures.get(group).push({ adapter: run.adapter, signature: canonical(signature) });
  }
  for (const [group, entries] of signatures) {
    if (new Set(entries.map((entry) => entry.signature)).size > 1) {
      const [caseId, workflow] = group.split('|');
      failedCases.add(caseId);
      fail({ caseId, workflow, check: 'adapter-divergence', detail: entries.map((entry) => `${entry.adapter}: ${entry.signature}`).join(' / ') });
    }
  }
  const isFull = result.scope === 'full' && canonical(result.adapters) === canonical(caseSet.adapters);
  if (isFull) {
    const present = new Set(result.runs.map((run) => `${run.caseId}|${run.workflow}|${run.adapter}`));
    for (const key of plannedKeys(caseSet, caseSet.adapters)) {
      if (!present.has(key)) {
        failedCases.add(key.split('|')[0]);
        fail({ caseId: key.split('|')[0], check: 'missing-run', detail: key });
      }
    }
  }
  const browsers = browserIdentities(result.runs, fail);
  const { requirements, unknown } = requirementCoverage(caseSet, strategy, failedCases);
  for (const entry of unknown) fail({ caseId: entry.caseId, check: 'unknown-requirement', detail: entry.id });
  // Admission also needs the run to name committed bytes; a development run can pass without it.
  const admissionBlockers = [];
  if (!isFull) admissionBlockers.push('subset run');
  if (result.identity.git?.commit === null || result.identity.git?.workingTreeChanges?.length) {
    admissionBlockers.push(`uncommitted source: ${(result.identity.git?.workingTreeChanges ?? []).join('; ')}`);
  }
  return {
    schemaVersion: VERDICT_SCHEMA_VERSION,
    validator: { path: VALIDATOR_PATH, sha256: repoFileSha256(VALIDATOR_PATH) },
    caseSetVersion: caseSet.caseSetVersion,
    scope: isFull ? 'full' : 'subset',
    admitted: failures.length === 0 && admissionBlockers.length === 0,
    subsetPassed: failures.length === 0,
    admissionBlockers,
    requireCurrentSource,
    identity: result.identity,
    browsers,
    runsChecked: result.runs.length,
    failures,
    requirements,
  };
}

function writeVerdict(resultDir, options) {
  const verdict = validateResult(resultDir, options);
  writeFileSync(join(resultDir, 'verdict.json'), `${JSON.stringify(verdict, null, 2)}\n`);
  return verdict;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [resultDir, ...flags] = process.argv.slice(2);
  if (!resultDir) {
    console.error('usage: node qualification/validate.js <resultDir> [--require-current-source]');
    process.exit(2);
  }
  const verdict = validateResult(resultDir, { requireCurrentSource: flags.includes('--require-current-source') });
  console.log(JSON.stringify({ admitted: verdict.admitted, scope: verdict.scope, failures: verdict.failures }, null, 2));
  process.exit(verdict.admitted ? 0 : 1);
}

export { validateResult, writeVerdict };
