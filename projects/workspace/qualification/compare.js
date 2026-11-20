#!/usr/bin/env node
// Fawn workspace comparison runner.
//
// Runs the frozen scenarios in projects/workspace/config/browser-product-comparison-policy.json#workspaceComparison
// for the treatment (the workspace service through its Playwright adapter) and the control (the
// competent baseline in ./baseline), interleaved per repetition, each with its own fixture site
// and state. Both drive the same browser binary through the same driver and process shape.
// Writes comparison.json with raw rows, identities and the evaluation under frozen criteria.
//
// Usage: node qualification/compare.js [--out DIR] [--scenarios id,id]

import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadServiceConfig } from '../src/config.js';
import { startFixtureSite } from './fixture-site.js';
import { REPO_ROOT, executableIdentityKey, inspectBrowserProcesses, resultIdentity, waitForProfileRelease } from './identity.js';
import { startHost } from './service-client.js';
import { stageBrowserProfile, matchesSelectedBuild } from './browser-profile.js';

const POLICY_PATH = 'projects/workspace/config/browser-product-comparison-policy.json';
const CASE_SET_PATH = 'projects/workspace/config/fawn-workspace-qualification.json';
const DEFAULT_OUT_ROOT = 'bench/out/fawn-workspace-comparison';
const BASELINE_HOST = fileURLToPath(new URL('./baseline/baseline-host.js', import.meta.url));
const COMPARISON_SCHEMA_VERSION = 1;
const WORKSPACE_ID = 'ws-comparison';
const OWNER_ID = 'agent-a';
const SETTLE_MS = 300;
const SIDES = Object.freeze(['treatment', 'control']);
const TREATMENT_WORKFLOW_FILES = Object.freeze([
  'src/workflows/document-research.js',
  'src/workflows/form-submission.js',
  'src/workflows/artifact-export.js',
  'src/workflows/owner-session.js',
]);
const CONTROL_WORKFLOW_FILES = Object.freeze(['qualification/baseline/baseline-workflows.js']);
const WORKSPACE_ROOT = fileURLToPath(new URL('../', import.meta.url));
const TREATMENT_RECOVERY = Object.freeze({ form: 'form-recovery', export: 'export-recovery' });

function parseArgs(argv) {
  const options = {};
  const allowed = ['out', 'scenarios', 'browser-channel', 'browser-config'];
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    if (!flag.startsWith('--') || !allowed.includes(flag.slice(2)) || !argv[index + 1] || argv[index + 1].startsWith('--')) {
      throw new Error(`Unknown or incomplete comparison argument: ${flag}`);
    }
    options[flag.slice(2)] = argv[index + 1];
  }
  return { out: options.out ?? null, scenarios: options.scenarios ? options.scenarios.split(',') : null,
    browserChannel: options['browser-channel'] ?? null, browserConfig: options['browser-config'] ?? null };
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  if (sorted.length === 0) return null;
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function codeLines(relativePath) {
  return readFileSync(join(WORKSPACE_ROOT, relativePath), 'utf8').split('\n')
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('//') && !line.startsWith('*') && !line.startsWith('/*')).length;
}

/** The same task for both sides; the control also receives the selectors its locators need. */
function buildTask(caseSet, scenario, site, runId) {
  const wf = caseSet.workflows[scenario.workflow];
  const base = site.origin;
  const builders = {
    research: () => ({ runId, intent: wf.intent, indexUrl: `${base}${wf.task.indexPath}`, topics: wf.task.topics, maxDocuments: wf.task.maxDocuments }),
    form: () => ({
      runId,
      intent: wf.intent,
      formUrl: `${base}${wf.task.formPath}`,
      fields: { name: `${wf.task.subjectPrefix} ${runId}`, email: wf.task.email },
      completedWhen: wf.task.completedWhen,
      failedWhen: wf.task.failedWhen,
      submissionsUrl: `${base}/submissions`,
      submissionsSelector: '#submissions',
      submitName: 'Send',
      completedSelector: '#receipt',
      failedSelector: '#error',
    }),
    export: () => ({ runId, intent: wf.intent, exportUrl: `${base}${scenario.pagePath ?? wf.task.exportPath}`, linkText: wf.task.linkText }),
  };
  return builders[scenario.workflow]();
}

function beforeEffectFor(scenario, site) {
  if (scenario.fault === 'background-settle') return { controlUrl: null, settleMs: SETTLE_MS };
  if (scenario.fault === 'replace-target') return { controlUrl: `${site.origin}/control/live?state=replaced`, settleMs: SETTLE_MS };
  return null;
}

class Side {
  constructor({ name, caseSet, policy, site, browserChannel, browserConfig }) {
    this.browserChannel = browserChannel;
    this.browserConfig = browserConfig;
    this.name = name;
    this.caseSet = caseSet;
    this.policy = policy;
    this.site = site;
    this.stateDir = join(mkdtempSync(join(tmpdir(), `fawn-comparison-${name}-`)), 'state');
    this.host = null;
    this.owner = null;
    this.inspections = [];
    this.actionTimeoutMs = loadServiceConfig().dispatch.actionTimeoutMs;
  }

  async start() {
    if (this.name === 'treatment') {
      this.host = await startHost({ stateDir: this.stateDir, adapter: this.policy.browserRuntime.treatmentAdapter,
        browserChannel: this.browserChannel, browserConfig: this.browserConfig, headless: this.policy.browserRuntime.headless });
      if (!this.owner) await this.setup();
    } else {
      this.host = await startHost({
        stateDir: this.stateDir,
        allowedOrigins: [this.site.origin],
        actionTimeoutMs: this.actionTimeoutMs,
        headless: this.policy.browserRuntime.headless,
        browserChannel: this.browserChannel, browserConfig: this.browserConfig,
      }, BASELINE_HOST);
    }
  }

  async setup() {
    const { adminCredential } = await this.host.call('createWorkspace', { workspaceId: WORKSPACE_ID });
    for (const [name, wf] of Object.entries(this.caseSet.workflows)) {
      await this.host.call('grantAuthorization', {
        workspaceId: WORKSPACE_ID,
        adminCredential,
        grantId: `${OWNER_ID}-${name}`,
        ownerId: OWNER_ID,
        intents: [wf.intent],
        actionKinds: wf.actionKinds,
        targetOrigins: [this.site.origin],
      });
    }
    const assigned = await this.host.call('assignOwner', { workspaceId: WORKSPACE_ID, adminCredential, ownerId: OWNER_ID });
    this.owner = { workspaceId: WORKSPACE_ID, ownerId: OWNER_ID, ownerGeneration: assigned.ownerGeneration, ownerCredential: assigned.ownerCredential };
  }

  /** One workflow call; resolves with the result or the error, plus observation bytes. */
  run(scenario, workflow, task) {
    const beforeEffect = beforeEffectFor(scenario, this.site);
    const request = this.name === 'treatment'
      ? this.host.request('measuredWorkflow', {
        name: workflow,
        owner: this.owner,
        task,
        fault: beforeEffect ? {
          kind: 'before-effect-control',
          actionIdSuffix: this.caseSet.workflows[scenario.workflow].effectActionSuffix,
          ...beforeEffect,
        } : null,
        sessionOptions: { observationRegions: scenario.treatmentRegions ?? [] },
      })
      : this.host.request('workflow', { name: workflow, task, beforeEffect });
    return request.then((value) => ({ ...value, error: null }), (error) => ({ result: null, observationBytes: null, error: { code: error.code ?? null, message: error.message } }));
  }

  /** The treatment resumes through each workflow's recovery; the control reruns with its progress file. */
  recoveryWorkflow(scenario) {
    return this.name === 'treatment' ? TREATMENT_RECOVERY[scenario.workflow] : scenario.workflow;
  }

  async kill() {
    this.host.kill();
    await this.host.exited;
    this.host = null;
    await waitForProfileRelease(this.stateDir);
  }

  inspect() {
    this.inspections.push(inspectBrowserProcesses(this.host.pid, this.stateDir));
  }

  async close() {
    if (this.host) {
      await this.host.request('close', {}).catch(() => {});
      await this.host.exited;
    }
    await waitForProfileRelease(this.stateDir);
    rmSync(join(this.stateDir, '..'), { recursive: true, force: true });
  }
}

/** Run one repetition: a clean task, a fault before the effect, or a kill while the effect is held. */
async function runRepetition(side, scenario, repetition) {
  await fetch(`${side.site.origin}/control/live?state=ready`);
  const runId = `${scenario.id}-${side.name}-${repetition}`;
  const task = buildTask(side.caseSet, scenario, side.site, runId);
  const from = side.site.requests.length;
  const started = performance.now();
  let outcome;
  let recovered = null;
  if (scenario.fault === 'kill-while-effect-held') {
    const held = side.site.hold(side.caseSet.workflows[scenario.workflow].effectRequest);
    const interrupted = side.run(scenario, scenario.workflow, task);
    await held.reached;
    await side.kill();
    held.release();
    await interrupted;
    await side.start();
    outcome = await side.run(scenario, side.recoveryWorkflow(scenario), task);
    recovered = true;
  } else {
    outcome = await side.run(scenario, scenario.workflow, task);
  }
  const latencyMs = performance.now() - started;
  side.inspect();
  return { task, outcome, latencyMs, requests: side.site.requests.slice(from), recovered };
}

const ORACLES = Object.freeze({
  'research-findings': ({ outcome, requests }, caseSet) => {
    const titles = outcome.result?.findings?.map((finding) => finding.title) ?? null;
    const foreign = requests.filter((entry) => entry.server === 'foreign').length;
    return {
      taskSuccess: outcome.result?.status === 'completed' && JSON.stringify(titles) === JSON.stringify(caseSet.oracles.researchFindingTitles) && foreign === 0,
      incorrectActions: foreign,
    };
  },
  'single-receipt': ({ outcome, task }, caseSet, site) => {
    const receipts = site.receipts.filter((receipt) => receipt.fields.name === task.fields.name).length;
    return { taskSuccess: outcome.result?.status === 'completed' && receipts === 1, incorrectActions: Math.max(0, receipts - 1) };
  },
  'report-artifact': ({ outcome }, caseSet) => {
    const saved = outcome.result?.artifact?.sha256 ?? null;
    const expected = caseSet.oracles.reportSha256['/export/report.csv'];
    return { taskSuccess: saved === expected, incorrectActions: saved !== null && saved !== expected ? 1 : 0 };
  },
  'no-replaced-artifact': ({ outcome, requests }, caseSet) => {
    const replaced = caseSet.oracles.reportSha256['/export/report-v2.csv'];
    const saved = outcome.result?.artifact?.sha256 ?? null;
    const servedReplaced = requests.filter((entry) => entry.kind === 'download' && entry.sha256 === replaced).length;
    return { taskSuccess: false, incorrectActions: (saved === replaced ? 1 : 0) + (saved === replaced ? 0 : servedReplaced) };
  },
});

function evaluateScenario(scenario, rows, criteria) {
  const bySide = Object.fromEntries(SIDES.map((name) => [name, rows.filter((row) => row.side === name)]));
  const count = (name, field) => bySide[name].filter((row) => row[field] === true).length;
  const sum = (name, field) => bySide[name].reduce((total, row) => total + row[field], 0);
  const measures = {
    taskSuccess: { treatment: count('treatment', 'taskSuccess'), control: count('control', 'taskSuccess'), higherIsBetter: true },
    incorrectActions: { treatment: sum('treatment', 'incorrectActions'), control: sum('control', 'incorrectActions'), higherIsBetter: false },
  };
  if (scenario.fault === 'kill-while-effect-held') {
    measures.recovery = { treatment: count('treatment', 'recovered'), control: count('control', 'recovered'), higherIsBetter: true };
  }
  const findings = [];
  for (const [measure, values] of Object.entries(measures)) {
    if (!criteria.materialWhenDifferent.includes(measure) || values.treatment === values.control) continue;
    const better = values.higherIsBetter ? values.treatment > values.control : values.treatment < values.control;
    findings.push({ measure, direction: better ? 'advantage' : 'regression', treatment: values.treatment, control: values.control });
  }
  const latency = Object.fromEntries(SIDES.map((name) => [name, median(bySide[name].map((row) => row.latencyMs))]));
  const rule = criteria.latency;
  const delta = latency.treatment - latency.control;
  let latencyFinding = 'no-material-difference';
  if (latency.treatment > latency.control * rule.regressionRatio && delta > rule.minimumDeltaMs) latencyFinding = 'regression';
  if (latency.treatment < latency.control * rule.advantageRatio && -delta > rule.minimumDeltaMs) latencyFinding = 'advantage';
  if (latencyFinding !== 'no-material-difference') findings.push({ measure: 'completeTaskLatencyMs', direction: latencyFinding, treatment: latency.treatment, control: latency.control });
  return {
    scenarioId: scenario.id,
    measures,
    medianLatencyMs: latency,
    serviceOverheadMs: delta,
    medianObservationBytes: Object.fromEntries(SIDES.map((name) => [name, median(bySide[name].map((row) => row.observationBytes).filter((bytes) => bytes !== null))])),
    findings,
  };
}

async function runScenario(scenario, { caseSet, policy, outDir, browserChannel, browserConfig }) {
  const sides = {};
  for (const name of SIDES) {
    const site = await startFixtureSite();
    sides[name] = new Side({ name, caseSet, policy, site, browserChannel, browserConfig });
    await sides[name].start();
    // A warm-up task opens the browser so repetitions compare warm sessions.
    await sides[name].run({ ...scenario, fault: 'none' }, scenario.workflow, buildTask(caseSet, { ...scenario, pagePath: undefined }, site, `${scenario.id}-${name}-warmup`));
  }
  const rows = [];
  for (let repetition = 1; repetition <= scenario.repetitions; repetition += 1) {
    const order = repetition % 2 ? SIDES : [...SIDES].reverse();
    for (const name of order) {
      const side = sides[name];
      const run = await runRepetition(side, scenario, repetition);
      const oracle = ORACLES[scenario.oracle](run, caseSet, side.site);
      rows.push({
        scenarioId: scenario.id,
        side: name,
        repetition,
        ...oracle,
        recovered: run.recovered ? oracle.taskSuccess && oracle.incorrectActions === 0 : null,
        latencyMs: run.latencyMs,
        observationBytes: run.outcome.observationBytes,
        status: run.outcome.result?.status ?? null,
        error: run.outcome.error,
        requestCount: run.requests.length,
      });
    }
  }
  const evidenceDir = join(outDir, 'scenarios', scenario.id);
  mkdirSync(evidenceDir, { recursive: true });
  const inspections = {};
  for (const name of SIDES) {
    const side = sides[name];
    inspections[name] = side.inspections;
    writeFileSync(join(evidenceDir, `${name}-fixture.json`), `${JSON.stringify({ requests: side.site.requests, receipts: side.site.receipts }, null, 2)}\n`);
    await side.close();
    await side.site.close();
  }
  return { rows, inspections };
}

function browserIdentity(inspectionsBySide) {
  return Object.fromEntries(SIDES.map((name) => {
    const executables = new Map();
    for (const inspection of inspectionsBySide[name]) {
      for (const executable of inspection.executables) executables.set(executableIdentityKey(executable), executable);
    }
    return [name, [...executables.values()]];
  }));
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const policyText = readFileSync(join(REPO_ROOT, POLICY_PATH), 'utf8');
  const policy = JSON.parse(policyText).workspaceComparison;
  const caseSet = JSON.parse(readFileSync(join(REPO_ROOT, CASE_SET_PATH), 'utf8'));
  const stamp = new Date().toISOString().replace(/[:.]/g, '').slice(0, 15);
  const outDir = options.out ?? join(REPO_ROOT, DEFAULT_OUT_ROOT, `${stamp}Z`);
  mkdirSync(outDir, { recursive: true });
  if (options.browserConfig && options.browserChannel) throw new Error('choose browser config or channel');
  const profile = stageBrowserProfile(options.browserConfig, outDir);
  if (profile && profile.config.browser.headless !== policy.browserRuntime.headless) throw new Error('profile must preserve frozen comparison headless mode');
  loadServiceConfig(profile?.path ?? undefined, { browserChannel: options.browserChannel });
  const identity = resultIdentity();
  if (profile) identity.browserLaunchConfig = profile.identity;
  const scenarios = policy.scenarios.filter((scenario) => !options.scenarios || options.scenarios.includes(scenario.id));
  const rows = [];
  const inspections = { treatment: [], control: [] };
  for (const scenario of scenarios) {
    const result = await runScenario(scenario, { caseSet, policy, outDir,
      browserChannel: options.browserChannel, browserConfig: profile?.path });
    rows.push(...result.rows);
    for (const name of SIDES) inspections[name].push(...result.inspections[name]);
    console.log(`ran: ${scenario.id}`);
  }
  const browsers = browserIdentity(inspections);
  const sameBrowser = JSON.stringify(browsers.treatment.map(executableIdentityKey)) === JSON.stringify(browsers.control.map(executableIdentityKey))
    && browsers.treatment.length === 1 && matchesSelectedBuild(profile?.config, browsers.treatment);
  const evaluation = scenarios.map((scenario) => evaluateScenario(scenario, rows.filter((row) => row.scenarioId === scenario.id), policy.criteria));
  const comparison = {
    schemaVersion: COMPARISON_SCHEMA_VERSION,
    comparisonVersion: policy.comparisonVersion,
    scope: options.scenarios ? 'subset' : 'full',
    identity,
    browserChannel: profile?.config.browser.channel ?? options.browserChannel ?? loadServiceConfig().browser.channel,
    browsers,
    equalOpportunityChecks: {
      sameBrowserBinary: sameBrowser,
      debuggingEndpoints: [...inspections.treatment, ...inspections.control]
        .reduce((total, inspection) => total + inspection.listeningTcpSockets + inspection.devToolsActivePortFiles, 0),
    },
    integrationLines: {
      treatment: Object.fromEntries(TREATMENT_WORKFLOW_FILES.map((path) => [path, codeLines(path)])),
      control: Object.fromEntries(CONTROL_WORKFLOW_FILES.map((path) => [path, codeLines(path)])),
    },
    excludedScenarios: policy.excludedScenarios,
    evaluation,
    rows,
  };
  writeFileSync(join(outDir, 'comparison.json'), `${JSON.stringify(comparison, null, 2)}\n`);
  for (const entry of evaluation) {
    const findings = entry.findings.map((finding) => `${finding.measure} ${finding.direction} (${Math.round(finding.treatment)} vs ${Math.round(finding.control)})`);
    console.log(`${entry.scenarioId}: success ${entry.measures.taskSuccess.treatment}/${entry.measures.taskSuccess.control}, `
      + `incorrect ${entry.measures.incorrectActions.treatment}/${entry.measures.incorrectActions.control}, `
      + `median ms ${Math.round(entry.medianLatencyMs.treatment)}/${Math.round(entry.medianLatencyMs.control)}; `
      + `${findings.length ? findings.join('; ') : 'no material difference'}`);
  }
  console.log(`same browser binary: ${sameBrowser}; ${join(outDir, 'comparison.json')}`);
  process.exit(sameBrowser ? 0 : 1);
}

if (process.argv.includes('--help')) console.log('Usage: node qualification/compare.js [--out DIR] [--scenarios id,id] [--browser-channel CHANNEL | --browser-config PATH]');
else await main();
