#!/usr/bin/env node
// A real investigation whose sources change underneath it: an agent reads this repository's code and
// a public documentation page and records competing explanations; it is interrupted; the repository
// moves from one pinned commit to a later one; a different agent resumes and has to finish on the
// sources as they now are. Fawn product client versus stock Chrome plus a durable tracker that is
// told which files changed. Same planners, tools, task text and read-only limits.
//
// The repository is a directory holding the investigated files as they are at --before, rewritten to
// --after between the sessions, so the same run can be repeated by anyone with these two commits.
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync, cpSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright-core';
import { WorkspaceService } from '../src/service.js';
import { loadServiceConfig } from '../src/config.js';
import { createPlaywrightAdapter } from '../src/adapters/playwright-adapter.js';
import { closeWithin, profileBrowserPids } from '../src/adapters/bounded-close.js';
import { queryPage, snapshotArgs, buildSnapshot } from '../src/adapters/page-query.js';
import { WorkspaceController, navigationNotice } from '../src/client/controller.js';
import { InvestigationStore } from '../src/client/investigation.js';
import { startAgent, investigationContext } from '../src/client/agent.js';
import { createCliPlanner } from '../src/client/cli-planner.js';
import { PLANNER_TOOLS } from '../src/client/planner.js';
import { repositoryEvidence, repositoryFiles } from '../src/client/repository.js';
import { listArtifacts } from '../src/client/artifact-memory.js';
import { readArtifact } from '../src/client/artifact-read.js';
import { describeChange, unfinishedRecords } from '../src/client/validity.js';
import { sha256Hex } from '../src/journal.js';
import { validateStockProposal, recoverStockProposal } from './real-handoff-stock.js';
import { judgeChangingSourceInvestigation, comparisonValidity, ACCEPTANCE } from './changing-source-judge.js';

const repoRoot = resolve(fileURLToPath(new URL('../../../', import.meta.url)));
const client = JSON.parse(readFileSync(join(repoRoot, 'projects/workspace/config/fawn-workspace-client.json')));
const help = 'Usage: node projects/workspace/qualification/changing-source-investigation.js --out DIR --before COMMIT --after COMMIT [--arms fawn,stock] [--max-cost-usd 12, split equally between arms] [--max-request-usd 1.5]';
const args = process.argv.slice(2);
if (args.includes('--help')) { console.log(help); process.exit(0); }
const value = (flag, fallback = null) => { const i = args.indexOf(flag); return i < 0 ? fallback : args[i + 1]; };
if (!value('--out') || !value('--before') || !value('--after')) throw Error(help);
const out = resolve(value('--out'));
if (existsSync(join(out, 'changing-source-investigation.json'))) throw Error('Never overwrite a retained trial');
mkdirSync(out, { recursive: true, mode: 0o700 });
const git = (cwd, ...command) => execFileSync('git', command, { cwd, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe'] }).trim();
const before = git(repoRoot, 'rev-parse', value('--before')), after = git(repoRoot, 'rev-parse', value('--after'));
const arms = value('--arms', 'fawn,stock').split(',');

// The public package's own source, as installed here. It is not in git, so it is copied into the
// investigated directory at the path a developer would read it from.
const PACKAGE = 'projects/workspace/node_modules/playwright-core';
const PACKAGE_FILES = ['package.json', 'lib/server/browserType.js', 'lib/server/browser.js', 'lib/server/browserContext.js',
  'lib/server/utils/processLauncher.js', 'lib/server/chromium/crBrowser.js'];
const SOURCES = ['projects/workspace/src/adapters/bounded-close.js', 'projects/workspace/src/adapters/playwright-adapter.js',
  'projects/workspace/src/adapters/cdp-adapter.js', 'docs/status/fawn-workspace.md',
  `${PACKAGE}/lib/server/browserType.js`, `${PACKAGE}/lib/server/browser.js`, `${PACKAGE}/lib/server/utils/processLauncher.js`,
  `${PACKAGE}/lib/server/chromium/crBrowser.js`, `${PACKAGE}/lib/server/browserContext.js`];
const DOCS_URL = 'https://playwright.dev/docs/api/class-browsercontext', origin = new URL(DOCS_URL).origin;
// The files whose change the investigation has to absorb, known from the two commits.
const changedBetween = git(repoRoot, 'diff', '--name-only', before, after).split('\n').filter(path => SOURCES.includes(path));
if (!changedBetween.length) throw Error('None of the investigated sources differ between --before and --after');

// Fixed before running. The per-request cap exists to stop a runaway request, not to shape the result:
// at 0.5 it ended the control's first agent on the request after it observed the documentation page
// (0.501), before anything was recorded. A request stopped by it now invalidates the pair.
const maxRequestCostUsd = Number(value('--max-request-usd', '1.5'));
if (!(maxRequestCostUsd > 0)) throw Error('Invalid per-request cap');
const REQUIRED_COMPLETION = Object.freeze({ requiredRecords: Object.freeze({ finding: 1, hypothesis: 2, question: 1, decision: 1 }) });
const POLICY = Object.freeze({ firstModel: 'claude-opus-5-5', resumeModel: 'claude-sonnet-5-5', firstTurns: 18, resumeTurns: 24,
  maxTotalCostUsd: Number(value('--max-cost-usd', '12')), maxArmCostUsd: Number(value('--max-cost-usd', '12')) / arms.length, maxRequestCostUsd, before, after, sources: SOURCES, changedSources: changedBetween, docsUrl: DOCS_URL,
  requiredCompletion: REQUIRED_COMPLETION,
  interruptAfter: 'a record rests on evidence from a source that changes between the two commits', acceptance: ACCEPTANCE });
const GOAL = 'Explain why releasing a Fawn workspace can stall for minutes on stock Chrome, and what each browser adapter does about it.';
const TASK = 'Investigate why releasing a Fawn workspace (closing its browser) can stall for minutes on stock Chrome, whether each of the two browser adapters is exposed, and what each does about it. '
  + 'This task is read-only: only navigate, and never enter a credential. '
  + `Read these sources with repository_read: ${SOURCES.join(', ')}. Also capture the public Playwright documentation for a browser context at ${DOCS_URL} (pageId main). `
  + 'More than one explanation is possible: record each one as a hypothesis, then support or reject it with a reason and the evidence it rests on. Do not drop a rejected explanation. '
  + 'Record findings that depend on the evidence: what the measurements in the status document show, what the Playwright source does when a persistent context is closed and whether it has a deadline, '
  + 'and for each adapter (Playwright and CDP) whether its release is bounded and how. Record a finding that gives a procedure someone else could run to reproduce the stall and to confirm the cause. '
  + 'Record what is still unknown as open questions, and one decision naming the next action. Then finish.';
const TASK_RESUME = 'Resume this investigation after an interruption; days have passed and the repository has moved on. Complete whatever remains of the original task. '
  + `Do not redo finished work, but every conclusion must hold for the sources as they are now. The original task was: ${TASK}`;
const NOTE = 'Days have passed and the repository has new commits since the last session. Continue and finish.';

const announce = message => console.log(`[${new Date().toISOString()}] ${message}`);
// The tracker's log is a summary, as the Fawn handoff is: long inputs and outputs are clipped, and their content stays in the saved records.
const logClip = value => { const text = typeof value === 'string' ? value : JSON.stringify(value ?? null); return text.length <= 400 ? value : `${text.slice(0, 400)}…`; };
// Each arm has its own equal share of the ceiling. A shared running total let the arm that ran first
// use up the allowance of the arm that ran second.
const spentBy = Object.fromEntries(arms.map(arm => [arm, 0]));
const totalSpent = () => Object.values(spentBy).reduce((sum, value) => sum + value, 0);
const calls = [];
function planner(arm, phase, model, tools = PLANNER_TOOLS) {
  const provider = createCliPlanner({ executable: process.env.FAWN_CLAUDE_BIN ?? 'claude', model, tools,
    directory: join(out, arm, `planner-${phase}`), config: { ...client, cliMaxBudgetUsd: maxRequestCostUsd } });
  return { identity: provider.identity, async next(context, options) {
    if (spentBy[arm] + maxRequestCostUsd > POLICY.maxArmCostUsd) throw Error('Run spend ceiling reached');
    const started = performance.now();
    try {
      const result = await provider.next(context, options);
      spentBy[arm] += result.usage?.costUsd ?? maxRequestCostUsd;
      calls.push({ arm, phase, model, tool: result.tool, ms: performance.now() - started, costUsd: result.usage?.costUsd ?? null, models: result.usage?.models });
      return result;
    } catch (error) {
      spentBy[arm] += error.usage?.costUsd ?? maxRequestCostUsd;
      calls.push({ arm, phase, model, error: error.message, ms: performance.now() - started, costUsd: error.usage?.costUsd ?? null });
      throw error;
    }
  } };
}

// The investigated repository is a plain directory holding the investigated files as they are at
// one commit, written with `git show`. No git command ever runs inside it. A linked worktree is not
// used: this checkout is a submodule with a relative core.worktree setting, and in a linked worktree
// git resolved the top level to the git directory and compared paths against the main checkout.
function materialize(repository, commit) {
  for (const path of SOURCES.filter(source => !source.startsWith(PACKAGE))) {
    mkdirSync(dirname(join(repository, path)), { recursive: true });
    writeFileSync(join(repository, path), execFileSync('git', ['show', `${commit}:${path}`], { cwd: repoRoot, maxBuffer: 64 * 1024 * 1024 }));
  }
}
function prepareRepository(dir) {
  const repository = join(dir, 'repository');
  materialize(repository, before);
  for (const file of PACKAGE_FILES) {
    mkdirSync(dirname(join(repository, PACKAGE, file)), { recursive: true });
    cpSync(join(repoRoot, PACKAGE, file), join(repository, PACKAGE, file));
  }
  return repository;
}
const moveRepository = repository => materialize(repository, after);

function fawnArm(dir, repository) {
  const stateDir = join(dir, 'service'), clientDir = join(dir, 'client');
  const config = loadServiceConfig(undefined, { browserChannel: 'chrome', headless: true });
  let service, controller, adapter, id = null;
  const navigate = () => controller.navigate(id, { pageId: 'main', url: DOCS_URL });
  return {
    name: 'fawn',
    async open() {
      service = await WorkspaceService.open({ stateDir, config, createAdapter: options => (adapter = createPlaywrightAdapter(options)) });
      controller = new WorkspaceController({ service, stateDir: clientDir, config: client });
      await controller.restore();
      if (!id) ({ id } = await controller.create({ goal: GOAL, repositoryRoot: repository }));
      try { await navigate(); } catch (error) { if (!/Take over/.test(error.message)) throw error; await controller.takeOver(id); await navigate(); }
    },
    async start({ model, phase, task, turns, resume }) {
      controller.planner = planner('fawn', phase, model); controller.config = { ...client, maxTurns: turns };
      await controller.delegate(id, { pageIds: ['main'], origins: [origin], actionKinds: ['navigate'], task, resume, requiredCompletion: REQUIRED_COMPLETION });
    },
    wait: () => controller.active.get(id)?.done,
    project: () => controller.store.get(id),
    lastSeq: () => controller.store.journal.records.at(-1).seq,
    note: text => controller.humanNote(id, text),
    async interrupt() { controller.active.get(id)?.controller.abort(Error('Interrupted')); await adapter.close({ timeoutMs: 0 }); await this.wait(); },
    async abandon() { controller.store.close(); await service.close().catch(() => {}); },
    async close() { await controller.close({ release: () => service.close() }); },
  };
}

function stockArm(dir, repository) {
  const profile = join(dir, 'profile'), trackerDir = join(dir, 'tracker'), projectId = 'stock-investigation';
  let context, page, store, run = null, abort = null, created = false;
  const fail = message => { const error = Error(message); error.code = 'STOCK_PROPOSAL_INVALID'; error.details = { neverDispatched: { code: error.code } }; throw error; };
  // What a competent setup already has: which saved files differ from the checkout now (git diff --numstat).
  const repositoryChanges = async () => {
    const changes = [];
    for (const artifact of Object.values(store.get(projectId).artifacts).filter(item => item.kind === 'evidence' && item.source?.kind === 'repository')) {
      const live = await repositoryEvidence(repository, artifact.source.path, client.maxEvidenceBytes).catch(() => null);
      if (!live) changes.push({ path: artifact.source.path, deleted: true });
      else if (live.sha256 !== artifact.source.sha256) {
        const { removedLines, addedLines } = describeChange(artifact.source.content, live.content);
        if (!changes.some(entry => entry.path === artifact.source.path)) changes.push({ path: artifact.source.path, removedLines, addedLines });
      }
    }
    return changes;
  };
  return {
    name: 'stock-chrome-and-tracker',
    async open() {
      context = await chromium.launchPersistentContext(profile, { channel: 'chrome', headless: true });
      page = context.pages()[0] ?? await context.newPage();
      store = new InvestigationStore(trackerDir);
      if (!created) { store.create({ id: projectId, goal: GOAL, repositoryRoot: repository }); created = true; }
      await page.goto(DOCS_URL).catch(() => {});
    },
    async start({ model, phase, task, turns, resume }) {
      const pages = new Map([['main', page]]), observations = new Map();
      let observationCount = 0;
      const startSequence = resume ? 0 : store.journal.records.at(-1).seq;
      const all = () => new Set(Object.keys(store.get(projectId).artifacts));
      const changes = resume ? await repositoryChanges() : null;
      const execute = async (tool, input) => {
        if (tool === 'repository_files') return repositoryFiles(repository, client.maxRepositoryFiles);
        if (tool === 'artifact_list') return listArtifacts(store.get(projectId), input, all());
        if (tool === 'artifact_read') return readArtifact(store.get(projectId), input, all());
        const validated = validateStockProposal(tool, input, pages, observations);
        input = validated.input;
        if (tool === 'observe' || tool === 'capture') {
          const snap = buildSnapshot(await page.evaluate(queryPage, snapshotArgs(loadServiceConfig(), { outline: true })), pages.size);
          observations.set('main', snap);
          // A version lets the shared context builder supersede and age this observation exactly as it does for the Fawn arm.
          if (tool === 'observe') return { pageId: 'main', url: snap.url, title: snap.title, observationVersion: ++observationCount, isTruncated: snap.isTruncated, text: snap.text,
            elements: snap.elements.filter(e => e.handle).map(({ handle, selector, role, label, value, inputType, href }) => ({ handle, selector, role, label, value, inputType, href })) };
          return store.revise(projectId, { kind: 'evidence', text: `Page evidence: ${snap.title || snap.url}`,
            source: { kind: 'page', pageId: 'main', url: snap.url, capturedAt: new Date().toISOString(), content: snap.text, sha256: sha256Hex(snap.text) } });
        }
        // The tracker is the same durable store: a source re-read into its existing record marks dependents for review.
        if (tool === 'repository_read') return store.revise(projectId, { ...(input.artifactId ? { id: input.artifactId, expectedRevision: input.expectedRevision ?? 0 } : {}),
          kind: 'evidence', text: `Repository evidence: ${input.path}`, source: await repositoryEvidence(repository, input.path, client.maxEvidenceBytes) });
        if (tool === 'record') return store.revise(projectId, input);
        if (input.kind !== 'navigate') fail('This task is read-only: only navigate is permitted');
        if (new URL(input.target.url).origin !== origin) fail('Navigation outside the permitted site');
        const response = await page.goto(input.target.url); observations.delete('main');
        return navigationNotice(input, { ok: true, url: page.url(), evidence: { effect: { status: response?.status() ?? null } } });
      };
      const tools = { ...PLANNER_TOOLS }; delete tools.reconcile; delete tools.handoff_read; delete tools.sources_check;
      tools.repository_read = `${tools.repository_read} To re-read a file into its existing evidence record, also pass artifactId and expectedRevision.`;
      abort = new AbortController();
      run = startAgent({ projectId, store, planner: planner('stock', phase, model, tools), config: { ...client, maxTurns: turns }, execute,
        requiredCompletion: REQUIRED_COMPLETION, recoverToolError: recoverStockProposal, signal: abort.signal, assertCurrent() {},
        // The control gets the same check the product makes: a finish that leaves marked records unrevised is returned once.
        reviewFinish: () => unfinishedRecords(store.get(projectId)), context: () => ({
          ...investigationContext(store.get(projectId), { task, permissions: { pageIds: ['main'], origins: [origin], actionKinds: ['navigate'] },
            initialArtifacts: new Set(), startSequence, shareRecords: true }),
          ...(resume ? { repositoryChanges: { note: 'Files saved as evidence that differ from the repository now.', files: changes },
            trackerLog: store.get(projectId).activity.filter(e => ['tool-requested', 'tool-result', 'tool-failed', 'human-note', 'finish', 'ask_human'].includes(e.event))
              .map(({ seq, event, tool, input, output, text, error }) => ({ seq, event, tool, input: logClip(input), output: output?.id ? { artifactId: output.id, kind: output.kind } : logClip(output), text, error })) } : {}) }) });
    },
    wait: () => run?.done,
    project: () => store.get(projectId),
    lastSeq: () => store.journal.records.at(-1).seq,
    note: text => store.activity(projectId, { event: 'human-note', text }),
    async interrupt() {
      abort?.abort(Error('Interrupted'));
      for (const pid of profileBrowserPids(profile)) { try { process.kill(pid, 'SIGKILL'); } catch { /* already gone */ } }
      await this.wait();
    },
    async abandon() { store.close(); await Promise.race([context.close().catch(() => {}), delay(2000)]); },
    async close() { store.close(); await closeWithin(context, { profileDir: profile, timeoutMs: 15_000 }); },
  };
}

async function runArm(name, dir) {
  const row = { arm: name === 'fawn' ? 'fawn' : 'stock-chrome-and-tracker' }, agentMs = {};
  const repository = prepareRepository(dir), arm = name === 'fawn' ? fawnArm(dir, repository) : stockArm(dir, repository);
  const timed = async (key, task) => { const started = performance.now(); try { return await task(); } finally { agentMs[key] = performance.now() - started; } };
  // Interrupt once some conclusion rests on a source that is about to change.
  const exposed = () => { const artifacts = arm.project().artifacts;
    const changing = Object.values(artifacts).filter(item => item.kind === 'evidence' && changedBetween.includes(item.source?.path)).map(item => item.id);
    return Object.values(artifacts).some(item => item.kind !== 'evidence' && item.dependsOn.some(id => changing.includes(id))); };
  try {
    await arm.open();
    await timed('first', async () => {
      await arm.start({ model: POLICY.firstModel, phase: 'first', task: TASK, turns: POLICY.firstTurns, resume: false });
      const finished = Promise.resolve(arm.wait()).then(() => true);
      for (;;) {
        if (await Promise.race([finished, delay(150).then(() => false)])) break;
        if (exposed()) { row.interrupted = true; await arm.interrupt(); break; }
      }
      await arm.wait();
    });
    row.firstRun = arm.project().run;
    const atInterruption = arm.project();
    row.recordsAtInterruption = Object.values(atInterruption.artifacts).filter(item => item.kind !== 'evidence').length;
    row.restingOnChangingSource = Object.values(atInterruption.artifacts).filter(item => item.kind !== 'evidence'
      && item.dependsOn.some(id => changedBetween.includes(atInterruption.artifacts[id]?.source?.path))).map(item => item.id);
    const boundaries = { interrupted: arm.lastSeq() };
    await arm.abandon();

    // The repository moves on while nobody is looking.
    moveRepository(repository);
    await arm.open();
    arm.note(NOTE);
    boundaries.resumeStarted = arm.lastSeq();
    await timed('resume', async () => {
      await arm.start({ model: POLICY.resumeModel, phase: 'resume', task: TASK_RESUME, turns: POLICY.resumeTurns, resume: true });
      await arm.wait();
    });
    const final = arm.project();
    row.finalRun = final.run; row.boundaries = boundaries;
    const liveHashes = Object.fromEntries(SOURCES.map(path => [path, sha256Hex(readFileSync(join(repository, path), 'utf8'))]));
    row.verdict = judgeChangingSourceInvestigation(final, { boundaries, liveHashes, changedSources: changedBetween, restingOnChangingSource: row.restingOnChangingSource });
    row.judgeProject = { artifacts: final.artifacts, activity: final.activity, run: final.run };
    await arm.close();
  } catch (error) {
    row.error = error.stack;
    await arm.abandon?.().catch(() => {});
  }
  const mine = calls.filter(call => call.arm === (name === 'fawn' ? 'fawn' : 'stock'));
  row.agentMs = agentMs; row.agentTotalMs = Object.values(agentMs).reduce((sum, ms) => sum + ms, 0);
  row.plannerCalls = mine.length; row.costUsd = mine.reduce((sum, call) => sum + (call.costUsd ?? 0), 0);
  row.resumeTools = mine.filter(call => call.phase === 'resume').map(call => call.tool ?? `error: ${call.error}`);
  row.plannerErrors = mine.filter(call => call.error).map(call => call.error);
  return row;
}

const rows = [];
for (const name of arms) {
  const dir = join(out, name); rmSync(dir, { recursive: true, force: true }); mkdirSync(dir, { recursive: true });
  announce(`Starting arm ${name}`);
  const row = await runArm(name, dir);
  rows.push(row);
  writeFileSync(join(out, `${name}-result.json`), JSON.stringify(row, null, 2));
  announce(`Finished arm ${name}: ${row.error ? 'error' : row.verdict.mechanicallyAccepted ? 'mechanical checks passed; diagnosis ungraded' : 'mechanical checks failed'}`);
}
const projection = row => row.error ? { arm: row.arm, error: row.error.split('\n')[0] } : { arm: row.arm, mechanicallyAccepted: row.verdict.mechanicallyAccepted,
  diagnosis: row.verdict.diagnosis, checks: row.verdict.checks, counts: row.verdict.counts, interrupted: row.interrupted === true,
  recordsAtInterruption: row.recordsAtInterruption, restingOnChangingSource: row.restingOnChangingSource.length,
  plannerCalls: row.plannerCalls, costUsd: row.costUsd, agentMs: row.agentMs, agentTotalMs: row.agentTotalMs, resumeTools: row.resumeTools };
const comparison = comparisonValidity(rows.map(row => ({ ...row, restingOnChangingSource: row.restingOnChangingSource ?? [] })));
const report = { schemaVersion: 1, classification: 'diagnostic: one paired investigation across a real source change', policy: POLICY, comparison,
  harnessCommit: git(repoRoot, 'rev-parse', 'HEAD'), harnessDirty: !!git(repoRoot, 'status', '--porcelain', '--', 'projects/workspace'),
  rows, calls, spentUsd: totalSpent(), spentByArmUsd: spentBy, publicProjection: rows.map(projection),
  limitations: ['One pair; model variance can flip any single verdict.',
    'The checks are mechanical: records exist, are intact, are linked and rest on current sources. Whether the diagnosis is correct is ungraded until a person grades it.',
    'The control is told which saved files changed; it is not given the list of records that rest on them.',
    'The first agent is stopped and its browser ended in-process; the owning process is not killed.',
    'The documentation page is live and may differ between arms and runs.'] };
writeFileSync(join(out, 'changing-source-investigation.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify({ report: join(out, 'changing-source-investigation.json'), spentUsd: totalSpent(), comparison, rows: report.publicProjection }, null, 1));
process.exit(rows.every(row => !row.error) ? 0 : 1);
