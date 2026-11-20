#!/usr/bin/env node
// Fawn workspace qualification runner.
//
// Runs every frozen case in projects/workspace/config/fawn-workspace-qualification.json against the service host
// through each declared adapter, with a fresh fixture site, state directory and browser profile
// per run. Writes result.json, per-run journals and fixture logs, then the validator's verdict.
//
// Usage: node qualification/run.js [--out DIR] [--adapters a,b] [--cases id,id] [--workflows w,w]

import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { loadServiceConfig } from '../src/config.js';
import { startFixtureSite } from './fixture-site.js';
import { REPO_ROOT, inspectBrowserProcesses, resultIdentity, waitForProfileRelease } from './identity.js';
import { PROCEDURES } from './procedures.js';
import { startHost } from './service-client.js';
import { summarizeAction, summarizeError, summarizeWorkflow } from './summaries.js';
import { writeVerdict } from './validate.js';
import { terminationEvidence } from './termination.js';
import { stageBrowserProfile } from './browser-profile.js';

const CASE_SET_PATH = 'projects/workspace/config/fawn-workspace-qualification.json';
const DEFAULT_OUT_ROOT = 'bench/out/fawn-workspace-qualification';
const WORKSPACE_ID = 'ws-qualification';
const RESULT_SCHEMA_VERSION = 1;
const NO_WORKFLOW = 'none';

function parseArgs(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!flag.startsWith('--') || value === undefined) throw new Error(`expected --flag value pairs, received ${flag}`);
    options[flag.slice(2)] = value;
  }
  const list = (name) => (options[name] ? options[name].split(',') : null);
  return {
    out: options.out ?? null,
    adapters: list('adapters'),
    cases: list('cases'),
    workflows: list('workflows'),
    browserChannel: options['browser-channel'] ?? null,
    browserConfig: options['browser-config'] ?? null,
    headless: options.headless === undefined ? undefined : options.headless !== 'false',
  };
}

const TASK_BUILDERS = Object.freeze({
  research: ({ wf, base, runId, intent }) => ({
    runId,
    intent,
    indexUrl: `${base}${wf.task.indexPath}`,
    topics: wf.task.topics,
    maxDocuments: wf.task.maxDocuments,
  }),
  form: ({ wf, base, runId, intent, token, overrides, options }) => {
    const subject = [wf.task.subjectPrefix, token, options.subjectSuffix].filter(Boolean).join(' ');
    const task = {
      runId,
      intent,
      formUrl: `${base}${wf.task.formPath}`,
      fields: {
        name: subject,
        email: overrides.email ?? wf.task.email,
        ...(options.reference ? { reference: options.reference } : {}),
      },
      completedWhen: wf.task.completedWhen,
      failedWhen: wf.task.failedWhen,
      submissionsUrl: `${base}${wf.task.submissionsPath}`,
      submissionsSelector: wf.task.submissionsSelector,
    };
    if (options.externalIdempotencyKey) task.externalIdempotencyKey = options.externalIdempotencyKey;
    if (options.resubmissionOf) task.resubmissionOf = options.resubmissionOf;
    return task;
  },
  export: ({ wf, base, runId, intent, overrides }) => ({
    runId,
    intent,
    exportUrl: `${base}${overrides.exportPath ?? wf.task.exportPath}`,
    linkText: wf.task.linkText,
  }),
});

function identityOf(owner) {
  const { workspaceId, ownerId, ownerGeneration, ownerCredential } = owner;
  return { workspaceId, ownerId, ownerGeneration, ownerCredential };
}

class RunContext {
  constructor({ caseSet, caseSpec, workflowName, adapter, site, runDir, token, browserChannel, browserConfig, headless }) {
    this.browserChannel = browserChannel;
    this.browserConfig = browserConfig;
    this.headless = headless;
    this.caseSet = caseSet;
    this.caseSpec = caseSpec;
    this.workflowName = workflowName;
    this.wf = caseSet.workflows[workflowName] ?? null;
    this.adapter = adapter;
    this.site = site;
    this.origin = site.origin;
    this.owners = caseSet.owners;
    this.runDir = runDir;
    this.token = token;
    this.stateDir = join(mkdtempSync(join(tmpdir(), `fawn-qualification-${adapter}-`)), 'state');
    this.journalPath = join(this.stateDir, loadServiceConfig().journal.fileName);
    this.steps = {};
    this.actionRefs = {};
    this.inspections = [];
    this.evidence = {};
    this.host = null;
    this.hostOpens = 0;
  }

  evidencePath(name) {
    return join(this.runDir, name);
  }

  async start(extra = {}) {
    this.host = await startHost({ stateDir: this.stateDir, adapter: this.adapter, browserChannel: this.browserChannel, browserConfig: this.browserConfig, headless: this.headless, ...extra });
    this.hostOpens += 1;
    return this.host;
  }

  /** Start a second host against the same state without replacing the current one. */
  startDetached() {
    return startHost({ stateDir: this.stateDir, adapter: this.adapter, browserChannel: this.browserChannel, browserConfig: this.browserConfig, headless: this.headless });
  }

  async close() {
    if (!this.host) return;
    await this.host.close();
    this.host = null;
    await waitForProfileRelease(this.stateDir);
  }

  /** SIGKILL the host (or await its own crash hook), then wait for its browser to exit. */
  async kill(pending = null, { killedByHost = false } = {}) {
    const host = this.host;
    if (!killedByHost) host.kill();
    const exit = await host.exited;
    if (pending) await pending;
    this.host = null;
    await waitForProfileRelease(this.stateDir);
    return terminationEvidence(exit, host.terminationRequest());
  }

  async setup() {
    await this.start();
    const { adminCredential } = await this.host.call('createWorkspace', { workspaceId: WORKSPACE_ID });
    for (const ownerId of this.owners) {
      for (const [name, wf] of Object.entries(this.caseSet.workflows)) {
        await this.host.call('grantAuthorization', {
          workspaceId: WORKSPACE_ID,
          adminCredential,
          grantId: `${ownerId}-${name}`,
          ownerId,
          intents: [wf.intent],
          actionKinds: wf.actionKinds,
          targetOrigins: [this.origin],
        });
      }
    }
    const owner = await this.assign(adminCredential, this.owners[0]);
    return { adminCredential, owner };
  }

  grantId(ownerId) {
    return `${ownerId}-${this.workflowName}`;
  }

  async assign(adminCredential, ownerId) {
    const assigned = await this.host.call('assignOwner', { workspaceId: WORKSPACE_ID, adminCredential, ownerId });
    return { workspaceId: WORKSPACE_ID, ...assigned };
  }

  identity(owner) {
    return identityOf(owner);
  }

  runId(n) {
    return `${this.token}-r${n}`;
  }

  effectId(runId) {
    return `${runId}${this.wf.effectActionSuffix}`;
  }

  task(runId, options = {}) {
    const overrides = this.caseSpec.taskOverrides ?? {};
    const base = overrides.origin === 'foreign' ? this.site.foreignOrigin : this.origin;
    return TASK_BUILDERS[this.workflowName]({
      wf: this.wf,
      base,
      runId,
      intent: overrides.intent ?? this.wf.intent,
      token: this.token,
      overrides,
      options,
    });
  }

  caseFault() {
    const fault = this.caseSpec.fault;
    if (!fault) return null;
    const located = { ...fault, actionIdSuffix: this.wf.effectActionSuffix };
    if (fault.kind === 'before-effect-control') {
      located.controlUrl = fault.liveState ? `${this.origin}/control/live?state=${fault.liveState}` : null;
    }
    return located;
  }

  sessionOptions() {
    return { observationRegions: this.caseSpec.sessionRegions ?? [] };
  }

  summarizeSettled(settled) {
    return settled.error
      ? { rejection: settled.error.code ?? null, message: settled.error.message }
      : summarizeWorkflow(this.workflowName, settled.value);
  }

  startWorkflow(owner, runId, { fault = null, task = {} } = {}) {
    return this.host.workflow(this.workflowName, identityOf(owner), this.task(runId, task), fault, this.sessionOptions())
      .then((result) => summarizeWorkflow(this.workflowName, result), summarizeError);
  }

  workflow(owner, runId, options) {
    return this.startWorkflow(owner, runId, options);
  }

  recover(owner, runId) {
    return this.host.workflow(`${this.workflowName}-recovery`, identityOf(owner), this.task(runId), null, this.sessionOptions())
      .then((result) => summarizeWorkflow(this.workflowName, result), summarizeError);
  }

  settle(promise) {
    return promise.then(() => ({ ok: true }), summarizeError);
  }

  async action(owner, actionId) {
    return summarizeAction(await this.host.call('action', { ...identityOf(owner), actionId }));
  }

  outstandingSummary(outstanding, refs) {
    return Object.fromEntries(Object.entries(refs).map(([name, actionId]) => [
      name,
      summarizeAction(outstanding.find((entry) => entry.actionId === actionId)),
    ]));
  }

  record(name, value) {
    this.steps[name] = value;
  }

  async inspect() {
    const inspection = inspectBrowserProcesses(this.host.pid, join(this.stateDir, 'profiles'));
    this.inspections.push(inspection);
    return inspection;
  }
}

function plannedRuns(caseSet, filters) {
  const runs = [];
  for (const caseSpec of caseSet.cases) {
    if (filters.cases && !filters.cases.includes(caseSpec.id)) continue;
    for (const workflowName of caseSpec.workflows) {
      if (filters.workflows && workflowName !== NO_WORKFLOW && !filters.workflows.includes(workflowName)) continue;
      for (const adapter of filters.adapters ?? caseSet.adapters) runs.push({ caseSpec, workflowName, adapter });
    }
  }
  return runs;
}

async function executeRun({ caseSet, caseSpec, workflowName, adapter, outDir, index, browserChannel, browserConfig, headless }) {
  const runDir = join(outDir, 'runs', caseSpec.id, workflowName, adapter);
  mkdirSync(runDir, { recursive: true });
  const site = await startFixtureSite();
  const token = `q${index}`;
  const ctx = new RunContext({ caseSet, caseSpec, workflowName, adapter, site, runDir, token, browserChannel, browserConfig, headless });
  const startedAt = new Date();
  let error = null;
  try {
    await PROCEDURES[caseSpec.procedure](ctx);
  } catch (caught) {
    error = { message: caught.message, code: caught.code ?? null, stack: caught.stack };
    if (ctx.host) await ctx.kill().catch(() => {});
  }
  if (!ctx.evidence.journal && existsSync(ctx.journalPath)) {
    copyFileSync(ctx.journalPath, join(runDir, 'journal.jsonl'));
    ctx.evidence.journal = 'journal.jsonl';
  }
  writeFileSync(join(runDir, 'fixture.json'), `${JSON.stringify({
    origin: site.origin,
    foreignOrigin: site.foreignOrigin,
    requests: site.requests,
    receipts: site.receipts,
    reportSha256: site.reportSha256,
  }, null, 2)}\n`);
  await site.close();
  rmSync(join(ctx.stateDir, '..'), { recursive: true, force: true });
  return {
    caseId: caseSpec.id,
    workflow: workflowName,
    adapter,
    token,
    origin: site.origin,
    startedAt: startedAt.toISOString(),
    durationMs: Date.now() - startedAt.getTime(),
    hostOpens: ctx.hostOpens,
    steps: ctx.steps,
    actionRefs: ctx.actionRefs,
    inspections: ctx.inspections,
    evidence: { directory: join('runs', caseSpec.id, workflowName, adapter), fixture: 'fixture.json', ...ctx.evidence },
    error,
  };
}

async function main() {
  const filters = parseArgs(process.argv.slice(2));
  const caseSet = JSON.parse(readFileSync(join(REPO_ROOT, CASE_SET_PATH), 'utf8'));
  const stamp = new Date().toISOString().replace(/[:.]/g, '').replace('T', 'T').slice(0, 15);
  const outDir = filters.out ?? join(REPO_ROOT, DEFAULT_OUT_ROOT, `${stamp}Z`);
  mkdirSync(outDir, { recursive: true });
  const identity = resultIdentity();
  if (filters.browserConfig && filters.browserChannel) throw new Error('choose --browser-config or --browser-channel, not both');
  if (filters.browserConfig && filters.headless !== undefined) throw new Error('set headless in the explicit browser profile');
  const profile = stageBrowserProfile(filters.browserConfig, outDir);
  if (profile) identity.browserLaunchConfig = profile.identity;
  const runs = [];
  const planned = plannedRuns(caseSet, filters);
  for (const [index, plan] of planned.entries()) {
    const run = await executeRun({ caseSet, ...plan, outDir, index, browserChannel: filters.browserChannel, browserConfig: profile?.path, headless: filters.headless });
    runs.push(run);
    console.log(`${run.error ? 'error' : 'ran'}: ${plan.caseSpec.id} ${plan.workflowName} ${plan.adapter} (${run.durationMs} ms)`
      + (run.error ? ` ${run.error.message}` : ''));
  }
  const result = {
    schemaVersion: RESULT_SCHEMA_VERSION,
    caseSetVersion: caseSet.caseSetVersion,
    scope: filters.cases || filters.workflows || filters.adapters ? 'subset' : 'full',
    browserChannel: profile?.config.browser.channel ?? filters.browserChannel ?? loadServiceConfig().browser.channel,
    headless: filters.headless ?? profile?.config.browser.headless ?? loadServiceConfig().browser.headless,
    filters,
    adapters: filters.adapters ?? caseSet.adapters,
    startedAt: runs[0]?.startedAt ?? null,
    identity,
    runs,
  };
  writeFileSync(join(outDir, 'result.json'), `${JSON.stringify(result, null, 2)}\n`);
  const verdict = writeVerdict(outDir);
  console.log(`verdict: ${verdict.admitted ? 'admitted' : 'not admitted'} (${verdict.scope}); `
    + `failures ${verdict.failures.length}; ${join(outDir, 'verdict.json')}`);
  for (const failure of verdict.failures) console.log(`  ${failure.caseId ?? '-'} ${failure.workflow ?? '-'} ${failure.adapter ?? '-'}: ${failure.check}: ${failure.detail}`);
  process.exit(verdict.scope === 'full' ? (verdict.admitted ? 0 : 1) : (verdict.subsetPassed ? 0 : 1));
}

await main();
