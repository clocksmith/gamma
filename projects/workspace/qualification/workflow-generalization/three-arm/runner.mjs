#!/usr/bin/env node
// Runner for the same-model three-arm test on OpenProject (clocksmith/deco#88).
//
//   node runner.mjs hash                                              # what step 1 of the freezing order posts; no cost
//   node runner.mjs preflight --run-dir D --approve-paid              # proves the session flags work, a few cents
//   node runner.mjs discovery --arm A --families F --run-dir D --approve-paid
//   node runner.mjs blind --arm A --families F --recipes R --run-dir D [--approve-paid]
//
// `discovery` and `blind` start a fresh instance for each arm, so no arm sees
// records another arm made. The runner never reads an answer key and writes no
// label. Every model session needs --approve-paid, and the runner refuses a
// session that could take the stage past its cap.
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import {
  appendFileSync, cpSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, realpathSync, statSync, writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { auditSessionLog, createAppSurface, DEFAULT_LIMITS } from './app-surface.mjs';
import { runGuard } from './guard-sandbox.mjs';
import * as instructions from './instructions.mjs';
import { openProjectRequester, provisionRecipe, readState, validateRecipe, validateRecipeFile } from './provision.mjs';
import { decide as decideWithBoundary } from './repair-boundary-arm.mjs';
import { FILE_TOOLS, runSession, sessionArgs } from './session.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const QUALIFICATION = resolve(HERE, '..');
export const ARMS = Object.freeze(['agent-written-guard', 'always-replan', 'repair-boundary']);

// Fixed before any family exists. Changing any of these changes the hash posted at step 1.
export const CONFIG = Object.freeze({
  application: 'openproject',
  upgrade: '13.4.0->14.0.0',
  model: 'claude-sonnet-5-5',
  stageCapUsd: 3.0,
  discovery: Object.freeze({ budgetUsd: 0.6, timeoutMs: 20 * 60 * 1000 }),
  route: Object.freeze({ budgetUsd: 0.08, timeoutMs: 3 * 60 * 1000 }),
  preflight: Object.freeze({ budgetUsd: 0.05, timeoutMs: 2 * 60 * 1000 }),
  limits: DEFAULT_LIMITS,
});

const sha256 = data => createHash('sha256').update(data).digest('hex');
const listFiles = dir => readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
  const path = join(dir, entry.name);
  return entry.isDirectory() ? listFiles(path) : entry.isFile() ? [path] : [];
}).sort();

/** One hash over a directory: every file's relative path and bytes, in a fixed order. */
export function hashDirectory(dir) {
  const hash = createHash('sha256');
  for (const file of listFiles(dir)) hash.update(relative(dir, file)).update('\0').update(readFileSync(file)).update('\0');
  return hash.digest('hex');
}

/** The files whose bytes fix how the arms are instructed, confined, run and recorded. */
export function frozenFileSet() {
  const files = [
    ...listFiles(HERE).filter(f => !f.endsWith('example-recipes.json')),
    ...listFiles(join(QUALIFICATION, 'bringup')),
    join(QUALIFICATION, 'same-model-three-arm-preregistration.md'),
    join(QUALIFICATION, 'repair-boundary-qualification.mjs'),
    join(QUALIFICATION, 'stage2-upstream-contract-probe.mjs'),
    resolve(QUALIFICATION, '../../src/client/repair-boundary.js'),
  ];
  const entries = files.map(file => ({ file: relative(resolve(QUALIFICATION, '../..'), file), sha256: sha256(readFileSync(file)) }));
  return { entries, sha256: sha256(entries.map(e => `${e.sha256}  ${e.file}\n`).join('')) };
}

function ledger(runDir, capUsd) {
  const file = join(runDir, 'spend.json');
  const read = () => (existsSync(file) ? JSON.parse(readFileSync(file, 'utf8')) : { spentUsd: 0, sessions: [] });
  return {
    reserve(label, budgetUsd) {
      const now = read();
      if (now.spentUsd + budgetUsd > capUsd + 1e-9) {
        throw Error(`refusing ${label}: $${now.spentUsd.toFixed(4)} spent, a $${budgetUsd} session could pass the $${capUsd} stage cap`);
      }
    },
    record(label, costUsd, budgetUsd) {
      const now = read();
      // A session that reported no cost is charged its whole budget, so the cap can only be met early.
      const charged = Number.isFinite(costUsd) ? costUsd : budgetUsd;
      now.spentUsd = Number((now.spentUsd + charged).toFixed(6));
      now.sessions.push({ label, costUsd: Number.isFinite(costUsd) ? costUsd : null, chargedUsd: charged, at: new Date().toISOString() });
      writeFileSync(file, JSON.stringify(now, null, 2), { mode: 0o600 });
      return now.spentUsd;
    },
    spent: () => read().spentUsd,
  };
}

// The real path, not the symlinked one: the CLI reports file paths resolved, and the audit compares against this.
const newWorkDir = prefix => realpathSync(mkdtempSync(join(tmpdir(), prefix)));
const appendRecord = (runDir, name, record) => appendFileSync(join(runDir, name), JSON.stringify(record) + '\n');

function serverFor({ arm, phase, runDir, workDir, familyIds, label, stateFile }) {
  const surfaceLog = join(runDir, 'logs', `${label}.surface.jsonl`);
  const artifactFile = arm === 'repair-boundary' ? join(runDir, 'artifacts', 'repair-boundary.json') : null;
  return {
    surfaceLog, artifactFile,
    server: { command: process.execPath, args: [join(HERE, 'arm-server.mjs')],
      env: { GAMMATRON_ARM_SERVER: JSON.stringify({ arm, phase, workDir, familyIds, surfaceLog, artifactFile, stateFile, limits: CONFIG.limits }) } },
  };
}

function defaultDeps() {
  const bringup = join(QUALIFICATION, 'bringup');
  return {
    executable: process.env.GAMMATRON_CLAUDE_BIN ?? 'claude',
    stateFile: undefined,
    freshInstance() {
      execFileSync(join(bringup, 'openproject-down.sh'), { stdio: 'ignore' });
      execFileSync(join(bringup, 'openproject-up.sh'), { stdio: 'inherit', timeout: 15 * 60 * 1000 });
    },
    stopInstance() { execFileSync(join(bringup, 'openproject-down.sh'), { stdio: 'ignore' }); },
    async openWriter(state) {
      const { chromium } = await import('playwright-core');
      const { executeWorkWrite, login, readWorkPackageRow } = await import('./write-step.mjs');
      const browser = await chromium.launch({ channel: 'chrome', headless: true });
      const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
      const page = await login(context, state.new.url, state.username, state.password);
      return {
        browserVersion: browser.version(),
        readRow: id => readWorkPackageRow(state.new.pgUrl, id),
        write: route => executeWorkWrite(page, { baseUrl: state.new.url, pgUrl: state.new.pgUrl, route }),
        close: () => browser.close(),
      };
    },
    guardRunner: runGuard,
  };
}

function loadFamilies(file) {
  const document = JSON.parse(readFileSync(file, 'utf8'));
  if (!Array.isArray(document?.families) || !document.families.length) throw Error('families file must be { "families": [...] }');
  for (const family of document.families) {
    if (typeof family.familyId !== 'string' || typeof family.policy !== 'string') throw Error('each family needs familyId and policy');
    const problems = validateRecipe(family.disclosedExample);
    if (problems.length) throw Error(`disclosed example of ${family.familyId}: ${problems.join('; ')}`);
  }
  return document.families;
}

/** Builds each family's disclosed example on the current instance and returns what an arm is told. */
async function discloseFamilies(families, state, tag) {
  const request = openProjectRequester(state.new);
  const disclosed = [];
  for (const family of families) {
    const built = await provisionRecipe(family.disclosedExample, { request, seed: state.new.seed, tag: `${tag}-${family.familyId}` });
    disclosed.push({ familyId: family.familyId, policy: family.policy,
      example: { project: built.project, workPackageId: built.workPackageId, workHours: built.workHours } });
  }
  return disclosed;
}

function prepare(runDir) {
  for (const sub of ['logs', 'artifacts', 'work']) mkdirSync(join(runDir, sub), { recursive: true, mode: 0o700 });
}

async function modelSession({ deps, runDir, label, arm, phase, workDir, familyIds, systemPrompt, prompt, budget, mcpTools, fileTools, jsonSchema, spend }) {
  spend.reserve(label, budget.budgetUsd);
  const { server, surfaceLog, artifactFile } = serverFor({ arm, phase, runDir, workDir, familyIds, label, stateFile: deps.stateFile });
  const { args, allowedTools } = sessionArgs({ model: CONFIG.model, budgetUsd: budget.budgetUsd, systemPrompt, server, mcpTools, fileTools, jsonSchema });
  const sessionLog = join(runDir, 'logs', `${label}.session.jsonl`);
  const session = await runSession({ executable: deps.executable, args, cwd: workDir, prompt, logFile: sessionLog, timeoutMs: budget.timeoutMs });
  spend.record(label, session.costUsd, budget.budgetUsd);
  const audit = auditSessionLog(session.lines, { allowedTools, workDir });
  const surface = existsSync(surfaceLog) ? readFileSync(surfaceLog, 'utf8').trim().split('\n').filter(Boolean).map(l => JSON.parse(l)) : [];
  return { session, audit, surface, artifactFile };
}

/** Phase 1 for one arm: a fresh instance, the disclosed examples, one session, then the freeze. */
export async function discovery({ arm, familiesFile, runDir, approvePaid = false, deps = defaultDeps() }) {
  if (!ARMS.includes(arm)) throw Error(`arm must be one of ${ARMS.join(', ')}`);
  prepare(runDir);
  const families = loadFamilies(familiesFile);
  const base = { runId: runIdOf(runDir), application: CONFIG.application, upgrade: CONFIG.upgrade, arm, phase: 'discovery' };
  if (arm === 'always-replan') {
    const at = new Date().toISOString();
    const record = { schema: 'gammatron-three-arm-phase-record/v1', ...base, startedAt: at, endedAt: at, wallMs: 0, modelCalls: 0, modelTurns: 0,
      costUsd: 0, budgetUsd: 0, recordsCreated: 0, outOfSurfaceCalls: 0,
      artifactSha256: sha256(instructions.ALWAYS_REPLAN + JSON.stringify(instructions.DECISION_SCHEMA)), completed: true };
    appendRecord(runDir, 'phase-records.jsonl', record);
    return record;
  }
  if (!approvePaid) throw Error('discovery makes model calls: pass --approve-paid once the owner has approved the stage');
  const spend = ledger(runDir, CONFIG.stageCapUsd);
  spend.reserve(`discovery-${arm}`, CONFIG.discovery.budgetUsd);
  deps.freshInstance();
  try {
    const state = readState(deps.stateFile);
    const disclosed = await discloseFamilies(families, state, `d-${arm}`);
    const workDir = newWorkDir(`three-arm-${arm}-`);
    const guardArm = arm === 'agent-written-guard';
    const { session, audit, surface, artifactFile } = await modelSession({
      deps, runDir, label: `discovery-${arm}`, arm, phase: 'discovery', workDir, familyIds: families.map(f => f.familyId),
      systemPrompt: guardArm ? instructions.AGENT_WRITTEN_GUARD : instructions.REPAIR_BOUNDARY,
      prompt: instructions.discoveryBrief(disclosed), budget: CONFIG.discovery, spend,
      mcpTools: guardArm ? ['app_request', 'try_guard'] : ['app_request', 'set_read_plan', 'add_example', 'learn'],
      fileTools: FILE_TOOLS,
    });
    let artifactSha256 = null;
    if (guardArm) {
      const kept = join(runDir, 'artifacts', 'agent-written-guard');
      cpSync(workDir, kept, { recursive: true });
      if (existsSync(join(kept, 'guard.mjs'))) artifactSha256 = hashDirectory(kept);
    } else if (artifactFile && existsSync(artifactFile)) {
      artifactSha256 = sha256(readFileSync(artifactFile));
    }
    const record = { schema: 'gammatron-three-arm-phase-record/v1', ...base,
      startedAt: session.startedAt, endedAt: session.endedAt, wallMs: session.wallMs,
      modelCalls: session.modelCalls, modelTurns: session.modelTurns, costUsd: session.costUsd ?? CONFIG.discovery.budgetUsd,
      budgetUsd: CONFIG.discovery.budgetUsd,
      recordsCreated: surface.filter(e => e.method === 'POST' && e.status === 201 && /work_packages\/?(\?|$)/.test(e.path ?? '')).length,
      outOfSurfaceCalls: audit.outOfSurface.length, artifactSha256, completed: artifactSha256 !== null };
    appendRecord(runDir, 'phase-records.jsonl', record);
    writeFileSync(join(runDir, 'logs', `discovery-${arm}.summary.json`), JSON.stringify({ record, audit,
      session: { exitCode: session.exitCode, subtype: session.subtype, timedOut: session.timedOut, models: session.models }, workDir }, null, 2));
    return record;
  } finally {
    deps.stopInstance();
  }
}

/** Phase 2 for one arm: a fresh instance, every unseen route built once, the arm asked, the write made if told to. */
export async function blind({ arm, familiesFile, recipesFile, runDir, approvePaid = false, deps = defaultDeps() }) {
  if (!ARMS.includes(arm)) throw Error(`arm must be one of ${ARMS.join(', ')}`);
  prepare(runDir);
  const families = loadFamilies(familiesFile);
  const document = JSON.parse(readFileSync(recipesFile, 'utf8'));
  const problems = validateRecipeFile(document);
  if (problems.length) throw Error(`recipes file: ${problems.join('; ')}`);
  const frozen = readFileSync(join(runDir, 'phase-records.jsonl'), 'utf8').trim().split('\n').map(l => JSON.parse(l))
    .findLast(r => r.arm === arm && r.phase === 'discovery');
  if (!frozen?.completed) throw Error(`${arm} has no frozen discovery artifact in this run`);
  const replans = arm === 'always-replan';
  if (replans && !approvePaid) throw Error('always-replan makes a model call per route: pass --approve-paid');
  const spend = ledger(runDir, CONFIG.stageCapUsd);
  const base = { runId: runIdOf(runDir), application: CONFIG.application, upgrade: CONFIG.upgrade, arm };
  const guardDir = join(runDir, 'artifacts', 'agent-written-guard');
  if (arm === 'agent-written-guard' && hashDirectory(guardDir) !== frozen.artifactSha256) throw Error('the guard changed after it was frozen');
  const boundaryText = arm === 'repair-boundary' ? readFileSync(join(runDir, 'artifacts', 'repair-boundary.json'), 'utf8') : null;
  if (boundaryText !== null && sha256(boundaryText) !== frozen.artifactSha256) throw Error('the learned guard changed after it was frozen');
  const startedAt = new Date();
  let costUsd = 0;
  let modelCalls = 0;
  let modelTurns = 0;
  let outOfSurfaceCalls = 0;
  deps.freshInstance();
  let writer = null;
  try {
    const state = readState(deps.stateFile);
    const request = openProjectRequester(state.new);
    const disclosed = replans ? await discloseFamilies(families, state, 'b') : [];
    writer = await deps.openWriter(state);
    for (const recipe of document.recipes) {
      const route = await provisionRecipe(recipe, { request, seed: state.new.seed, tag: `b-${recipe.routeId}` });
      const before = writer.readRow(route.workPackageId);
      const began = Date.now();
      let answer = { decision: 'stop', reason: null, reads: 0, modelCalls: 0, costUsd: 0, error: null };
      try {
        const surfaceLog = join(runDir, 'logs', `blind-${arm}.surface.jsonl`);
        const reader = () => createAppSurface({ mode: 'decision', request, limits: CONFIG.limits,
          log: entry => appendFileSync(surfaceLog, JSON.stringify({ arm, routeId: route.routeId, ...entry }) + '\n') }).tools.app_get;
        if (arm === 'agent-written-guard') {
          const get = reader();
          const result = await deps.guardRunner({ guardDir, route, get: path => get({ path }) });
          answer = { ...answer, decision: result.decision, reason: result.reason, reads: result.reads, error: result.error };
        } else if (arm === 'repair-boundary') {
          const get = reader();
          const result = await decideWithBoundary(JSON.parse(boundaryText), route, path => get({ path }));
          answer = { ...answer, ...result };
        } else {
          const family = disclosed.find(f => f.familyId === route.familyId);
          if (!family) throw Error(`route names an unknown family ${route.familyId}`);
          const workDir = newWorkDir('three-arm-replan-');
          const { session, audit, surface } = await modelSession({
            deps, runDir, label: `blind-always-replan-${route.routeId}`, arm, phase: 'decision', workDir, familyIds: [],
            systemPrompt: instructions.ALWAYS_REPLAN, prompt: instructions.routeBrief(family, route), budget: CONFIG.route, spend,
            mcpTools: ['app_get'], fileTools: [], jsonSchema: instructions.DECISION_SCHEMA,
          });
          outOfSurfaceCalls += audit.outOfSurface.length;
          modelTurns += session.modelTurns;
          const clean = !session.isError && audit.outOfSurface.length === 0 && ['write', 'stop'].includes(session.structured?.decision);
          answer = { decision: clean ? session.structured.decision : 'stop',
            reason: clean ? String(session.structured.reason ?? '').slice(0, 300) : null,
            reads: surface.filter(e => !e.refused).length, modelCalls: session.modelCalls,
            costUsd: session.costUsd ?? CONFIG.route.budgetUsd, error: clean ? null : `session ended as ${session.subtype}` };
        }
      } catch (error) {
        answer = { ...answer, decision: 'stop', error: String(error?.message ?? error).slice(0, 240) };
      }
      const decisionWallMs = Date.now() - began;
      const wrote = answer.decision === 'write' ? await writer.write(route) : null;
      const after = wrote ? wrote.after : writer.readRow(route.workPackageId);
      costUsd += answer.costUsd;
      modelCalls += answer.modelCalls;
      appendRecord(runDir, 'route-records.jsonl', {
        schema: 'gammatron-three-arm-route-record/v1', ...base, routeId: route.routeId,
        decision: answer.decision, stopReason: answer.decision === 'stop' ? (answer.reason ?? null) : null,
        writeAttempted: wrote !== null, httpStatus: wrote?.httpStatus ?? null, before, after,
        committed: after.lockVersion !== before.lockVersion,
        effectMatches: Number(after.estimatedHours) === Number(route.workHours),
        workHours: route.workHours, reads: answer.reads, modelCalls: answer.modelCalls, costUsd: answer.costUsd,
        decisionWallMs, artifactSha256: frozen.artifactSha256, error: answer.error ?? wrote?.error ?? null,
      });
    }
  } finally {
    await writer?.close();
    deps.stopInstance();
  }
  const endedAt = new Date();
  const record = { schema: 'gammatron-three-arm-phase-record/v1', ...base, phase: 'blind-routes',
    startedAt: startedAt.toISOString(), endedAt: endedAt.toISOString(), wallMs: endedAt - startedAt,
    modelCalls, modelTurns, costUsd: Number(costUsd.toFixed(6)), budgetUsd: replans ? CONFIG.route.budgetUsd * document.recipes.length : 0,
    recordsCreated: 0, outOfSurfaceCalls, artifactSha256: null, completed: true };
  appendRecord(runDir, 'phase-records.jsonl', record);
  return record;
}

/** A few cents: one tiny session per kind, to prove the flags give the tools we expect and nothing else. */
export async function preflight({ runDir, approvePaid = false, deps = defaultDeps() }) {
  if (!approvePaid) throw Error('preflight makes model calls: pass --approve-paid once the owner has approved the stage');
  prepare(runDir);
  const spend = ledger(runDir, CONFIG.stageCapUsd);
  deps.freshInstance();
  const results = [];
  try {
    for (const [arm, phase, mcpTools, fileTools] of [
      ['agent-written-guard', 'discovery', ['app_request', 'try_guard'], FILE_TOOLS],
      ['always-replan', 'decision', ['app_get'], []],
    ]) {
      const workDir = newWorkDir('three-arm-preflight-');
      const tool = phase === 'decision' ? 'app_get' : 'app_request';
      const { session, audit, surface } = await modelSession({
        deps, runDir, label: `preflight-${arm}`, arm, phase, workDir, familyIds: [], budget: CONFIG.preflight, spend, mcpTools, fileTools,
        systemPrompt: 'This is a tool check. Do exactly what the message says, then reply with the single word DONE.',
        prompt: `1. Call the ${tool} tool once to read /api/v3/statuses${phase === 'decision' ? '' : ' as the approver'}.`
          + (fileTools.length ? '\n2. Write a file named check.txt in your working directory containing the word ok.' : '')
          + '\n3. List every tool you have by name in your final reply before the word DONE.',
      });
      results.push({ arm, phase, exitCode: session.exitCode, subtype: session.subtype, costUsd: session.costUsd, models: session.models,
        toolCalls: audit.byTool, outOfSurface: audit.outOfSurface, surfaceCalls: surface.length,
        fileWritten: fileTools.length ? existsSync(join(workDir, 'check.txt')) : null, reply: session.text?.slice(0, 600) ?? null });
    }
  } finally {
    deps.stopInstance();
  }
  writeFileSync(join(runDir, 'preflight.json'), JSON.stringify({ spentUsd: spend.spent(), results }, null, 2));
  return results;
}

const runIdOf = runDir => `stageA-${resolve(runDir).split('/').pop()}`;

async function main(argv) {
  const [command, ...rest] = argv;
  const option = name => (rest.includes(name) ? rest[rest.indexOf(name) + 1] : undefined);
  const flag = name => rest.includes(name);
  if (command === 'hash') {
    const frozen = frozenFileSet();
    for (const entry of frozen.entries) console.log(`${entry.sha256}  ${entry.file}`);
    console.log(`\nrunner sha256: ${frozen.sha256}`);
    return;
  }
  const runDir = option('--run-dir');
  if (!runDir || !['preflight', 'discovery', 'blind'].includes(command)) {
    console.error('usage: runner.mjs hash | preflight --run-dir D | discovery --arm A --families F --run-dir D | blind --arm A --families F --recipes R --run-dir D  [--approve-paid]');
    process.exit(2);
  }
  mkdirSync(runDir, { recursive: true, mode: 0o700 });
  if (!statSync(runDir).isDirectory()) throw Error('run-dir is not a directory');
  const common = { runDir: resolve(runDir), approvePaid: flag('--approve-paid') };
  const result = command === 'preflight' ? await preflight(common)
    : command === 'discovery' ? await discovery({ ...common, arm: option('--arm'), familiesFile: option('--families') })
      : await blind({ ...common, arm: option('--arm'), familiesFile: option('--families'), recipesFile: option('--recipes') });
  console.log(JSON.stringify(result, null, 2));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main(process.argv.slice(2));
