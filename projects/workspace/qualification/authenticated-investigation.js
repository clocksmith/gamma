#!/usr/bin/env node
// Read-only investigation of one issue on a signed-in site, carried through an interruption, a lost
// sign-in, a person signing in again and a different agent finishing from the preserved evidence.
// Fawn product client versus stock Chrome plus a durable tracker, with the same planners, tools,
// task text and read-only limits. Acceptance is fixed in the judge before any arm runs.
//
// A person signs in directly in the browser window. No agent, planner, journal or report receives a
// credential. With --stand-in the site is a local rehearsal stand-in and the person is scripted.
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
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
import { sha256Hex } from '../src/journal.js';
import { validateStockProposal, recoverStockProposal } from './real-handoff-stock.js';
import { judgeAuthenticatedInvestigation, ACCEPTANCE } from './authenticated-investigation-judge.js';
import { harnessLimitErrors } from './changing-source-judge.js';
import { startStandInSite } from './authenticated-stand-in-site.js';

const repoRoot = resolve(fileURLToPath(new URL('../../../', import.meta.url)));
const client = JSON.parse(readFileSync(join(repoRoot, 'projects/workspace/config/fawn-workspace-client.json')));
const help = `Usage: node projects/workspace/qualification/authenticated-investigation.js --out DIR (--stand-in | --issue-url URL)
  [--arms fawn,stock] [--repository-root PATH --expected-code PATH,PATH] [--sign-in-url URL] [--auth-loss revoke|clear-cookies]
  [--sign-in-timeout-min 15] [--max-cost-usd 10] [--max-request-usd 1.5] [--headless] [--no-session-reuse]
A real site needs a person at this machine: the harness prints ACTION NEEDED lines and waits.
With --issue-url, name the repository checkout and the files the issue concerns; only those files count as code evidence.`;
const args = process.argv.slice(2);
if (args.includes('--help')) { console.log(help); process.exit(0); }
const FLAGS = ['--stand-in', '--headless', '--no-session-reuse'], VALUES = ['--out', '--issue-url', '--arms', '--repository-root', '--expected-code', '--sign-in-url', '--auth-loss', '--sign-in-timeout-min', '--max-cost-usd', '--max-request-usd'];
for (let i = 0; i < args.length; i++) {
  if (FLAGS.includes(args[i])) continue;
  if (VALUES.includes(args[i]) && args[i + 1] && !args[i + 1].startsWith('--')) { i++; continue; }
  throw Error(`Unknown or incomplete argument: ${args[i]}\n${help}`);
}
const value = (flag, fallback = null) => { const i = args.indexOf(flag); return i < 0 ? fallback : args[i + 1]; };
const standIn = args.includes('--stand-in');
if (!value('--out') || standIn === !!value('--issue-url')) throw Error(`Name an output directory and exactly one of --stand-in or --issue-url\n${help}`);
const out = resolve(value('--out'));
if (existsSync(join(out, 'authenticated-investigation.json'))) throw Error('Never overwrite a retained trial');
mkdirSync(out, { recursive: true, mode: 0o700 });
const arms = value('--arms', 'fawn,stock').split(',');
const headless = standIn || args.includes('--headless');
const repositoryRoot = value('--repository-root') ? resolve(value('--repository-root')) : null;
// How the sign-in is lost while the investigation is interrupted. clear-cookies removes the profile's
// cookies, which is what a forced browser exit can do and needs nobody; revoke asks the person to end
// the session at the site. Both leave the agent facing the same unreachable page.
const authLoss = value('--auth-loss', standIn ? 'site-forgets-sessions' : 'clear-cookies');
if (!(standIn ? ['site-forgets-sessions', 'clear-cookies'] : ['revoke', 'clear-cookies']).includes(authLoss)) throw Error(`Unsupported --auth-loss ${authLoss}`);
// The person signs in for the first arm only. Later arms start from, and are restored to, that same
// person's session, carried in this process's memory. It is never written to a file, a journal or a
// report, and never reaches a planner.
const reuseSession = !args.includes('--no-session-reuse');
const signInTimeoutMs = Number(value('--sign-in-timeout-min', '15')) * 60_000;

const site = standIn ? await startStandInSite() : null;
const issueUrl = standIn ? site.issueUrl : new URL(value('--issue-url')).href;
const origin = new URL(issueUrl).origin;
const signInUrl = standIn ? site.signInUrl : value('--sign-in-url',
  new URL(issueUrl).hostname === 'github.com' ? `${origin}/login?return_to=${encodeURIComponent(issueUrl)}` : issueUrl);
const FRESH = standIn ? 'Rolled back the TTL change on Tuesday' : null;
// Declared before running: the only sources that count as code evidence. On a real site these are
// named repository files, bound to their bytes in the checkout at the start of the run.
const expectedCode = (value('--expected-code') ?? '').split(',').map(path => path.trim()).filter(Boolean);
if (!standIn && (!repositoryRoot || !expectedCode.length)) throw Error(`A real-site trial needs --repository-root and --expected-code\n${help}`);
const CODE = standIn ? { kind: 'pages', urls: site.codeUrls }
  : { kind: 'repository', paths: expectedCode, hashes: Object.fromEntries(expectedCode.map(path => [path, sha256Hex(readFileSync(join(repositoryRoot, path), 'utf8'))])) };

// Fixed before running. The per-request cap stops a runaway request; it was 0.4, and the same kind of
// cap at 0.5 ended an arm of the changing-source trial one request after a large page was observed.
// A person's sign-ins are spent on this trial, so the cap is set well clear of an ordinary request and
// any request it does stop is reported as a harness limit, not as the arm's result.
const maxRequestCostUsd = Number(value('--max-request-usd', '1.5'));
if (!(maxRequestCostUsd > 0)) throw Error('Invalid per-request cap');
const POLICY = Object.freeze({
  firstModel: 'claude-opus-5-5', resumeModel: 'claude-sonnet-5-5', finishModel: 'claude-sonnet-5-5',
  // finishTurns was 12 in the first live rehearsal (ed2041f46c); both arms spent it before recording
  // everything the task asks for, so the finishing agent now gets the client's ordinary 20.
  // resumeTurns was 6 in the second (af1634bdf0): the Fawn arm's resuming agent spent it writing findings
  // from the preserved evidence and finished before it ever looked at the unreachable page.
  firstTurns: 14, resumeTurns: 12, finishTurns: 20, interruptAfter: 'issue page and one declared code source saved',
  maxTotalCostUsd: Number(value('--max-cost-usd', '10')), maxRequestCostUsd, authLoss, acceptance: ACCEPTANCE, code: CODE,
});
const GOAL = 'Produce a source-linked summary of one issue: the problem, the code involved, prior attempts and unresolved questions.';
const TASK = `Investigate the issue at ${issueUrl} (pageId main) and produce a source-linked summary. `
  + 'This task is read-only: only navigate. Never fill, click or submit anything, and never enter a credential. '
  + 'Capture the issue page as evidence. Identify the code it concerns and save that as evidence too: '
  + (repositoryRoot ? 'read the relevant files with repository_read. ' : 'navigate to the code pages the issue links to on the same site and capture each. ')
  + 'Then record: a finding summarizing the problem that depends on the issue evidence and the code evidence; a finding listing the prior attempts the issue mentions and why each fell short, or stating that none are recorded; '
  + 'at least one open question; and one decision naming the concrete next action. '
  + 'Last, navigate to the issue page again, capture it, and record a finding stating its current state (open or closed, number of comments, anything new since the first capture) that depends on that fresh capture. Then finish.';
const TASK_RESUME = 'Resume this investigation after an interruption; time has passed. Complete whatever remains of the original task; '
  + `do not redo finished work, and rely on the saved evidence where it exists. The original task was: ${TASK}`;

const announce = message => console.log(`[${new Date().toISOString()}] ${message}`);
// The tracker's log is a summary, as the Fawn handoff is: long inputs and outputs are clipped, and their content stays in the saved records.
const logClip = value => { const text = typeof value === 'string' ? value : JSON.stringify(value ?? null); return text.length <= 400 ? value : `${text.slice(0, 400)}…`; };
let spent = 0, credentialReachedPlanner = false;
const calls = [];
function planner(arm, phase, model, tools = PLANNER_TOOLS) {
  const provider = createCliPlanner({ executable: process.env.FAWN_CLAUDE_BIN ?? 'claude', model, tools,
    directory: join(out, arm, `planner-${phase}`), config: { ...client, cliMaxBudgetUsd: maxRequestCostUsd } });
  return { identity: provider.identity, async next(context, options) {
    if (spent + maxRequestCostUsd > POLICY.maxTotalCostUsd) throw Error('Run spend ceiling reached');
    if (site && JSON.stringify(context).includes(site.password)) credentialReachedPlanner = true;
    const started = performance.now();
    try {
      const result = await provider.next(context, options);
      spent += result.usage?.costUsd ?? maxRequestCostUsd;
      calls.push({ arm, phase, model, tool: result.tool, ms: performance.now() - started, costUsd: result.usage?.costUsd ?? null, models: result.usage?.models });
      return result;
    } catch (error) {
      spent += error.usage?.costUsd ?? maxRequestCostUsd;
      calls.push({ arm, phase, model, error: error.message, ms: performance.now() - started, costUsd: error.usage?.costUsd ?? null });
      throw error;
    }
  } };
}

// Whether this browser profile can read the issue right now. A background request with the
// profile's cookies: it never touches the page a person may be typing in.
async function signedIn(page) {
  const response = await page.context().request.get(issueUrl, { failOnStatusCode: false, timeout: 30_000 });
  return response.status() === 200 && new URL(response.url()).pathname === new URL(issueUrl).pathname;
}
async function waitUntil(check, label) {
  const deadline = Date.now() + signInTimeoutMs;
  while (!await check().catch(() => false)) {
    if (Date.now() > deadline) throw Error(`Timed out waiting for a person: ${label}`);
    await delay(3000);
  }
}
// The person at the machine. On the stand-in the same steps are scripted, typed into the page as a
// person would; the stand-in's password is generated per run and exists only in this process.
let carriedSession = null;
const humanSteps = [];
const expectedPersonSteps = standIn ? 0 : (reuseSession && authLoss === 'clear-cookies' ? 2 : arms.length * (authLoss === 'revoke' ? 3 : 2));
const person = {
  /**
   * @param why  what this sign-in is for, shown to the person
   * @param mayReuse  whether this arm may take the session a person already established in an earlier arm
   */
  async signIn(page, label, { why, mayReuse }) {
    const started = performance.now();
    const done = by => { humanSteps.push({ label, by, waitedMs: Math.round(performance.now() - started) }); return by; };
    if (mayReuse && reuseSession && carriedSession) {
      await page.context().addCookies(carriedSession);
      if (await signedIn(page)) { await page.goto(issueUrl).catch(() => {}); return done('session carried from the first arm'); }
    }
    await page.goto(signInUrl).catch(() => {});
    if (standIn) {
      await page.fill('#user', 'investigator'); await page.fill('#password', site.password);
      await Promise.all([page.waitForURL(url => url.pathname === new URL(issueUrl).pathname), page.click('#go')]);
    } else {
      const step = humanSteps.filter(entry => entry.by === 'person').length + 1;
      announce(`ACTION NEEDED (step ${step} of ${expectedPersonSteps}, ${label}): ${why} Sign in in the Chrome window that is showing ${new URL(signInUrl).host}. Waiting up to ${signInTimeoutMs / 60_000} minutes.`);
      await waitUntil(() => signedIn(page), `${label} sign-in`);
      announce(`Signed in (${label}).`);
    }
    carriedSession = await page.context().cookies([origin]);
    return done(standIn ? 'scripted person' : 'person');
  },
  // What happens to the sign-in while the investigation is interrupted.
  async loseSignInWhileAway() {
    if (!standIn) return;
    if (authLoss === 'site-forgets-sessions') site.forgetSessions();
    site.addComment('priya', `${FRESH}; large carts are slow again and support has two new reports.`);
  },
  async confirmSignedOut(page, label) {
    if (authLoss === 'clear-cookies') await page.context().clearCookies();
    if (authLoss === 'revoke' && await signedIn(page)) {
      announce(`ACTION NEEDED (${label}): end this trial browser's session from your usual browser (on GitHub: Settings, Sessions, then revoke the newest one). Waiting up to ${signInTimeoutMs / 60_000} minutes.`);
      await waitUntil(async () => !await signedIn(page), `${label} session revocation`);
    }
    if (await signedIn(page)) throw Error('The profile still has access; the sign-in was not lost');
  },
};

function fawnArm(dir) {
  const stateDir = join(dir, 'service'), clientDir = join(dir, 'client');
  const config = loadServiceConfig(undefined, { browserChannel: 'chrome', headless });
  let service, controller, adapter, id = null;
  const navigate = () => controller.navigate(id, { pageId: 'main', url: issueUrl });
  return {
    name: 'fawn',
    async open() {
      service = await WorkspaceService.open({ stateDir, config, createAdapter: options => (adapter = createPlaywrightAdapter(options)) });
      controller = new WorkspaceController({ service, stateDir: clientDir, config: client });
      await controller.restore();
      if (!id) ({ id } = await controller.create({ goal: GOAL, repositoryRoot }));
    },
    page: () => adapter._page(id, 'main'),
    // The person opens the issue through the workspace, taking control back from an agent first.
    async personOpensIssue() {
      try { await navigate(); } catch (error) { if (!/Take over/.test(error.message)) throw error; await controller.takeOver(id); await navigate(); }
    },
    async start({ model, phase, task, turns, resume }) {
      controller.planner = planner('fawn', phase, model); controller.config = { ...client, maxTurns: turns };
      await controller.delegate(id, { pageIds: ['main'], origins: [origin], actionKinds: ['navigate'], task, resume });
    },
    wait: () => controller.active.get(id)?.done,
    project: () => controller.store.get(id),
    lastSeq: () => controller.store.journal.records.at(-1).seq,
    note: text => controller.humanNote(id, text),
    // Interruption: the agent stops mid-task and the browser is ended with no time to exit.
    async interrupt() { controller.active.get(id)?.controller.abort(Error('Interrupted')); await adapter.close({ timeoutMs: 0 }); await this.wait(); },
    async abandon() { controller.store.close(); await service.close().catch(() => {}); },
    async close() { await controller.close({ release: () => service.close() }); },
    journals: () => [join(stateDir, 'journal.jsonl'), join(clientDir, 'investigations', 'investigation.jsonl')],
  };
}

function stockArm(dir) {
  const profile = join(dir, 'profile'), trackerDir = join(dir, 'tracker'), projectId = 'stock-investigation';
  let context, page, store, run = null, abort = null, created = false;
  const fail = message => { const error = Error(message); error.code = 'STOCK_PROPOSAL_INVALID'; error.details = { neverDispatched: { code: error.code } }; throw error; };
  return {
    name: 'stock-chrome-and-tracker',
    async open() {
      context = await chromium.launchPersistentContext(profile, { channel: 'chrome', headless });
      page = context.pages()[0] ?? await context.newPage();
      store = new InvestigationStore(trackerDir);
      if (!created) { store.create({ id: projectId, goal: GOAL, repositoryRoot }); created = true; }
    },
    page: () => page,
    async personOpensIssue() { await page.goto(issueUrl).catch(() => {}); },
    async start({ model, phase, task, turns, resume }) {
      const pages = new Map([['main', page]]), observations = new Map();
      let observationCount = 0;
      const startSequence = resume ? 0 : store.journal.records.at(-1).seq;
      const all = () => new Set(Object.keys(store.get(projectId).artifacts));
      const execute = async (tool, input) => {
        if (['repository_files', 'repository_read'].includes(tool) && !repositoryRoot) fail('No repository is available for this task');
        if (tool === 'repository_files') return repositoryFiles(repositoryRoot, client.maxRepositoryFiles);
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
        if (tool === 'repository_read') return store.revise(projectId, { kind: 'evidence', text: `Repository evidence: ${input.path}`, source: await repositoryEvidence(repositoryRoot, input.path, client.maxEvidenceBytes) });
        if (tool === 'record') return store.revise(projectId, input);
        // The same limits the workspace enforces for the Fawn arm: navigation only, inside the site.
        if (input.kind !== 'navigate') fail('This task is read-only: only navigate is permitted');
        if (new URL(input.target.url).origin !== origin) fail('Navigation outside the permitted site');
        const response = await page.goto(input.target.url); observations.delete('main');
        // The control reports the response status too; an unreachable page is how a lost sign-in shows.
        return navigationNotice(input, { ok: true, url: page.url(), evidence: { effect: { status: response?.status() ?? null } } });
      };
      const tools = { ...PLANNER_TOOLS }; delete tools.reconcile; delete tools.handoff_read;
      abort = new AbortController();
      // The durable tracker shows a resuming agent everything earlier sessions and the person recorded.
      run = startAgent({ projectId, store, planner: planner('stock', phase, model, tools), config: { ...client, maxTurns: turns }, execute,
        recoverToolError: recoverStockProposal, signal: abort.signal, assertCurrent() {}, context: () => ({
          ...investigationContext(store.get(projectId), { task, permissions: { pageIds: ['main'], origins: [origin], actionKinds: ['navigate'] },
            initialArtifacts: new Set(), startSequence, shareRecords: true }),
          ...(resume ? { trackerLog: store.get(projectId).activity.filter(e => ['tool-requested', 'tool-result', 'tool-failed', 'human-note', 'finish', 'ask_human'].includes(e.event))
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
    journals: () => [join(trackerDir, 'investigation.jsonl')],
  };
}

async function runArm(arm, firstArm) {
  const row = { arm: arm.name }, agentMs = {}, humanWaitMs = {};
  const timed = async (bucket, key, task) => { const started = performance.now(); try { return await task(); } finally { bucket[key] = performance.now() - started; } };
  const evidenceIds = () => Object.values(arm.project().artifacts).filter(value => value.kind === 'evidence').map(value => value.id);
  // The interruption comes once the issue page and one declared code source are saved, which is what
  // the first acceptance check asks for; an agent that never reads a declared source is not interrupted.
  const plain = url => String(url ?? '').split(/[?#]/)[0];
  const readyToInterrupt = () => {
    const evidence = Object.values(arm.project().artifacts).filter(value => value.kind === 'evidence');
    return evidence.some(value => value.source?.kind === 'page' && plain(value.source.url) === plain(issueUrl))
      && evidence.some(value => CODE.kind === 'pages' ? value.source?.kind === 'page' && CODE.urls.map(plain).includes(plain(value.source.url))
        : value.source?.kind === 'repository' && CODE.paths.includes(value.source.path));
  };
  const whole = performance.now();
  try {
    await arm.open();
    await arm.personOpensIssue();
    await timed(humanWaitMs, 'firstSignIn', () => person.signIn(arm.page(), `${arm.name}, first sign-in`,
      { why: 'The investigation needs a signed-in session to start.', mayReuse: !firstArm }));
    await arm.personOpensIssue();

    // Session A: a live model starts; once the issue and one code source are saved it is interrupted.
    await timed(agentMs, 'first', async () => {
      await arm.start({ model: POLICY.firstModel, phase: 'first', task: TASK, turns: POLICY.firstTurns, resume: false });
      const finished = Promise.resolve(arm.wait()).then(() => true);
      for (;;) {
        if (await Promise.race([finished, delay(150).then(() => false)])) break;
        if (readyToInterrupt()) { row.interrupted = true; await arm.interrupt(); break; }
      }
      await arm.wait();
    });
    row.firstRun = arm.project().run;
    const evidenceAtInterruption = evidenceIds(), boundaries = { interrupted: arm.lastSeq() };
    await arm.abandon();

    // Away: the site ends the session. Restart; the person reopens the issue and finds it unreachable.
    await person.loseSignInWhileAway();
    await arm.open();
    await timed(humanWaitMs, 'sessionLoss', () => person.confirmSignedOut(arm.page(), `${arm.name}, losing the sign-in`));
    await arm.personOpensIssue();
    boundaries.resumeStarted = arm.lastSeq();

    // Session B: a different model resumes without access.
    await timed(agentMs, 'resume', async () => {
      await arm.start({ model: POLICY.resumeModel, phase: 'resume', task: TASK_RESUME, turns: POLICY.resumeTurns, resume: true });
      await arm.wait();
    });
    row.resumeRun = arm.project().run;
    row.resumeToolSequence = arm.project().activity.filter(event => event.seq > boundaries.resumeStarted && event.event === 'tool-requested').map(event => event.tool);

    // The person signs in again and hands the work back; another agent finishes.
    if (row.resumeRun?.status !== 'completed') {
      const request = arm.project().activity.findLast(event => event.event === 'ask_human' && event.seq > boundaries.resumeStarted)?.text;
      await timed(humanWaitMs, 'secondSignIn', () => person.signIn(arm.page(), `${arm.name}, second sign-in`,
        { why: request ? `The agent lost access and asked: "${String(request).slice(0, 160)}"` : 'The agent stopped without access to the site.', mayReuse: !firstArm }));
      arm.note('Signed in again; continue.');
      await arm.personOpensIssue();
      boundaries.secondSignIn = arm.lastSeq();
      await timed(agentMs, 'finish', async () => {
        await arm.start({ model: POLICY.finishModel, phase: 'finish', task: TASK_RESUME, turns: POLICY.finishTurns, resume: true });
        await arm.wait();
      });
    } else boundaries.secondSignIn = arm.lastSeq();

    const final = arm.project();
    row.finalRun = final.run; row.boundaries = boundaries; row.evidenceAtInterruption = evidenceAtInterruption;
    row.verdict = judgeAuthenticatedInvestigation(final, { issueUrl, code: CODE, boundaries, evidenceAtInterruption, freshMarker: FRESH });
    row.judgeProject = { artifacts: final.artifacts, activity: final.activity, run: final.run };
    await arm.close();
    if (site) {
      row.credentialInJournals = arm.journals().some(file => readFileSync(file, 'utf8').includes(site.password));
      row.verdict.checks.credentialAbsent = !row.credentialInJournals && !credentialReachedPlanner;
      row.verdict.mechanicallyAccepted = Object.values(row.verdict.checks).every(Boolean);
    }
  } catch (error) {
    row.error = error.stack;
    await arm.abandon?.().catch(() => {});
  }
  const mine = calls.filter(call => call.arm === (arm.name === 'fawn' ? 'fawn' : 'stock'));
  row.agentMs = agentMs; row.humanWaitMs = humanWaitMs;
  row.plannerCalls = mine.length; row.costUsd = mine.reduce((sum, call) => sum + (call.costUsd ?? 0), 0);
  row.plannerMs = mine.reduce((sum, call) => sum + call.ms, 0);
  row.agentTotalMs = Object.values(agentMs).reduce((sum, ms) => sum + ms, 0);
  row.wallMs = performance.now() - whole;
  return row;
}

const rows = [];
try {
  for (const name of arms) {
    const dir = join(out, name); rmSync(dir, { recursive: true, force: true }); mkdirSync(dir, { recursive: true });
    announce(`Starting arm ${name}`);
    const row = await runArm(name === 'fawn' ? fawnArm(dir) : stockArm(dir), rows.length === 0);
    rows.push(row);
    // Persist each arm before the next begins; a later failure must not discard it.
    writeFileSync(join(out, `${name}-result.json`), JSON.stringify(row, null, 2));
    announce(`Finished arm ${name}: ${row.error ? 'error' : row.verdict.mechanicallyAccepted ? 'mechanical checks passed; diagnosis ungraded' : 'mechanical checks failed'}`);
  }
} finally { await site?.close(); }

const projection = row => row.error ? { arm: row.arm, error: row.error.split('\n')[0] } : { arm: row.arm, mechanicallyAccepted: row.verdict.mechanicallyAccepted, diagnosis: row.verdict.diagnosis, checks: row.verdict.checks,
  counts: row.verdict.counts, interrupted: row.interrupted === true, resumeToolSequence: row.resumeToolSequence, plannerCalls: row.plannerCalls,
  costUsd: row.costUsd, agentMs: row.agentMs, agentTotalMs: row.agentTotalMs, humanWaitMs: row.humanWaitMs };
const report = { schemaVersion: 1,
  classification: standIn ? 'rehearsal on a local stand-in site with a scripted person; not an external-site result'
    : 'diagnostic: one paired authenticated external-site investigation',
  policy: POLICY, target: standIn ? 'local stand-in' : { issueUrl, signInUrl }, repositoryRootUsed: repositoryRoot !== null, headless,
  sourceCommit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repoRoot, encoding: 'utf8' }).trim(),
  sourceDirty: !!execFileSync('git', ['status', '--porcelain', '--', 'projects/workspace'], { cwd: repoRoot, encoding: 'utf8' }).trim(),
  rows, calls, spentUsd: spent,
  // Requests a harness limit stopped. Any entry means the affected arm's result is the harness's, not the arm's.
  harnessLimits: [...new Set(calls.map(call => call.arm))].map(arm => ({ arm, errors: harnessLimitErrors(calls.filter(call => call.arm === arm && call.error).map(call => call.error)) }))
    .filter(entry => entry.errors.length),
  // Who established each sign-in. A carried session is the first arm's, restored from memory.
  humanSteps, sessionReuse: reuseSession ? 'the first arm\'s signed-in session was carried in process memory to later arms; it was not written anywhere' : 'disabled',
  // Counts and outcomes only: safe to copy into a public record. Everything else in this file can
  // contain the investigated site's content and stays local.
  publicProjection: rows.map(projection),
  limitations: ['One pair; model variance can flip any single verdict.',
    'The checks are mechanical: records exist, are intact and are linked. Whether the diagnosis is correct is ungraded until a person grades it (authenticated-investigation-grade.js).',
    'Read-only: no action with an uncertain outcome occurs, so outcome reconciliation is not exercised.',
    'The first agent is stopped and its browser ended in-process; the owning process is not killed.',
    ...(standIn ? ['The site is a local stand-in and the person is scripted.'] : ['Human waiting time is recorded separately and excluded from agent time.'])] };
const serialized = JSON.stringify(report, null, 2);
// The carried session is a credential. Refuse to write a report that contains any of it.
if ((carriedSession ?? []).some(cookie => typeof cookie.value === 'string' && cookie.value.length >= 8 && serialized.includes(cookie.value))) {
  throw Error('Refusing to write a report that contains session cookie values');
}
writeFileSync(join(out, 'authenticated-investigation.json'), serialized);
console.log(JSON.stringify({ report: join(out, 'authenticated-investigation.json'), spentUsd: spent, harnessLimits: report.harnessLimits, rows: report.publicProjection }, null, 1));
process.exit(rows.every(row => !row.error) ? 0 : 1);
