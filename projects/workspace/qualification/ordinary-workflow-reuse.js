#!/usr/bin/env node
// Ordinary browser workflow reuse benchmark across six common tasks and three repeats.
//
// Compares Fawn fresh planning (`mode: 'fresh'`) against saved-workflow reuse (`mode: 'reuse'`)
// after one verified learning pass (`mode: 'learn'`) per repeat, alongside a reference stock
// Playwright script floor. Raw outputs stay in ignored `fawn/.tmp/`.

import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
import { WorkspaceService } from '../src/service.js';
import { loadServiceConfig } from '../src/config.js';
import { createPlaywrightAdapter } from '../src/adapters/playwright-adapter.js';
import { WorkflowStore } from '../src/client/workflow-store.js';
import { InvestigationStore } from '../src/client/investigation.js';
import { createCliPlanner } from '../src/client/cli-planner.js';
import { WORKFLOW_SYSTEM, WORKFLOW_TOOLS } from '../src/client/workflow-agent.js';
import { canonicalJson, sha256Hex } from '../src/journal.js';
import {
  buildOrdinaryTaskSpecs,
  createControlledOrdinaryPlanner,
  startOrdinaryTasksServer,
} from './ordinary-tasks-site.js';

const USAGE = [
  'Usage: node projects/workspace/qualification/ordinary-workflow-reuse.js',
  '  --out .tmp/DIR [--simulatte ../simulatte] [--repeats 3]',
  '  [--max-calls 288] [--max-cost-usd 12] [--max-call-usd 0.15] [--controlled]',
].join('\n');

const rawArgs = process.argv.slice(2);
if (rawArgs.includes('--help')) {
  console.log(USAGE);
  process.exit(0);
}

const VALUE_FLAGS = new Set(['--out', '--simulatte', '--repeats', '--max-calls', '--max-cost-usd', '--max-call-usd']);
const BOOL_FLAGS = new Set(['--controlled']);
const parsedFlags = new Map();
for (let i = 0; i < rawArgs.length; i += 1) {
  const token = rawArgs[i];
  if (BOOL_FLAGS.has(token)) {
    parsedFlags.set(token, true);
    continue;
  }
  if (VALUE_FLAGS.has(token) && rawArgs[i + 1] && !rawArgs[i + 1].startsWith('--')) {
    parsedFlags.set(token, rawArgs[i + 1]);
    i += 1;
    continue;
  }
  throw Error(`Invalid argument: ${token}\n${USAGE}`);
}

if (!parsedFlags.has('--out')) throw Error(`--out is required\n${USAGE}`);

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const out = resolve(root, parsedFlags.get('--out'));
const simulatteRepo = resolve(root, parsedFlags.get('--simulatte') ?? '../simulatte');
const controlled = Boolean(parsedFlags.get('--controlled'));
const repeats = Number.parseInt(String(parsedFlags.get('--repeats') ?? '3'), 10);
const maxModelCalls = Number.parseInt(String(parsedFlags.get('--max-calls') ?? '288'), 10);
const maxCostUsd = Number(parsedFlags.get('--max-cost-usd') ?? '12');
const maxCallUsd = Number(parsedFlags.get('--max-call-usd') ?? '0.15');

if (!Number.isInteger(repeats) || repeats < 1 || repeats > 3) {
  throw Error('repeats must be an integer in 1..3');
}
if (!Number.isInteger(maxModelCalls) || maxModelCalls < 1) {
  throw Error('max-calls must be a positive integer');
}
if (!Number.isFinite(maxCostUsd) || maxCostUsd <= 0 || !Number.isFinite(maxCallUsd) || maxCallUsd <= 0) {
  throw Error('max-cost-usd and max-call-usd must be positive numbers');
}
if (existsSync(join(out, 'frozen.json'))) {
  throw Error(`Refusing to overwrite existing trial directory: ${out}`);
}

mkdirSync(out, { recursive: true, mode: 0o700 });

const clientConfig = JSON.parse(readFileSync(join(root, 'projects/workspace/config/fawn-workspace-client.json'), 'utf8'));
const serviceConfig = loadServiceConfig(undefined, { browserChannel: 'chrome', headless: true });
serviceConfig.observation.maxElements = 1000;

const sourcePaths = [
  'projects/workspace/config/fawn-workspace-client.json',
  'projects/workspace/config/fawn-workspace-service.json',
  'projects/workspace/qualification/ordinary-workflow-reuse.js',
  'projects/workspace/qualification/ordinary-tasks-site.js',
  ...[
    'client/workflow-agent',
    'client/workflow-store',
    'client/trace-dag',
    'client/trace-graph-dp',
    'client/agent',
    'client/cli-planner',
    'client/investigation',
    'adapters/page-query',
    'adapters/playwright-adapter',
    'adapters/bounded-close',
    'service',
  ].map((p) => `projects/workspace/src/${p}.js`),
];
const sourceHashes = Object.fromEntries(
  sourcePaths.map((p) => [p, sha256Hex(readFileSync(join(root, p)))]),
);
const selfHash = sourceHashes['projects/workspace/qualification/ordinary-workflow-reuse.js'];
const siteHash = sourceHashes['projects/workspace/qualification/ordinary-tasks-site.js'];

const specs = buildOrdinaryTaskSpecs();
const server = await startOrdinaryTasksServer({ simulatteRepo });

const ceilings = {
  maxModelCalls,
  maxCostUsd,
  maxCallUsd,
  maxTurnsPerRun: 16,
  declaredModel: controlled ? 'controlled-ordinary-preflight' : 'sonnet',
};

const frozen = {
  schema: 'fawn.ordinary-workflow-reuse/v1',
  startedAt: new Date().toISOString(),
  controlled,
  repeats,
  ceilings,
  simulatteRevision: server.simulatteRevision,
  sourceCommit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
  sourceDirty: Boolean(execFileSync('git', ['status', '--porcelain'], { cwd: root, encoding: 'utf8' }).trim()),
  sourceHashes,
  tasks: specs.map(({ id, category, template, routePath, fields, intermediateClicks, learnInputs, evalInputs }) => ({
    id,
    category,
    template,
    routePath,
    slotCount: fields.length,
    clickCount: intermediateClicks.length,
    learnInputs: learnInputs.slice(0, repeats),
    evalInputs: evalInputs.slice(0, repeats),
  })),
  claimBoundary: 'Measures Fawn saved-workflow reuse against Fawn fresh planning across six ordinary local tasks over three independent cold-store repeats, with a reference Playwright script floor. Stock Chrome in all arms; no Doe GPU, Chromium-fork or live-external-site claim.',
};
writeFileSync(join(out, 'frozen.json'), `${JSON.stringify(frozen, null, 2)}\n`);
console.log(JSON.stringify({ event: 'ceiling-declared', controlled, repeats, tasks: specs.length, ceilings }));

const calls = [];
const rows = [];
let spentUpperBoundUsd = 0;

function makePlanner(runName, spec) {
  const provider = controlled
    ? createControlledOrdinaryPlanner(spec)
    : createCliPlanner({
        executable: process.env.FAWN_CLAUDE_BIN ?? 'claude',
        model: 'sonnet',
        directory: join(out, runName, 'planner'),
        config: { ...clientConfig, cliMaxBudgetUsd: maxCallUsd },
        system: WORKFLOW_SYSTEM,
        tools: WORKFLOW_TOOLS,
      });
  return {
    identity: provider.identity,
    async next(...params) {
      if (!controlled && calls.length + 1 > maxModelCalls) {
        throw Error(`Model call ceiling reached (${maxModelCalls})`);
      }
      if (!controlled && spentUpperBoundUsd + maxCallUsd > maxCostUsd) {
        throw Error(`Campaign spend ceiling reached ($${maxCostUsd})`);
      }
      const started = performance.now();
      if (!controlled) spentUpperBoundUsd += maxCallUsd;
      const record = { run: runName, taskId: spec.id, startedAt: new Date().toISOString(), status: 'started' };
      calls.push(record);
      try {
        const proposal = await provider.next(...params);
        record.status = 'completed';
        record.tool = proposal.tool;
        record.usage = proposal.usage ?? null;
        if (
          !controlled
          && (!proposal.usage?.models?.length
            || proposal.usage.models.some((m) => !m.toLowerCase().includes('sonnet')))
        ) {
          throw Error('Missing Sonnet model attestation from CLI planner');
        }
        return proposal;
      } catch (error) {
        record.status = 'failed';
        record.error = error.message;
        record.usage ??= error.usage ?? null;
        throw error;
      } finally {
        record.elapsedMs = performance.now() - started;
        if (!controlled && Number.isFinite(record.usage?.costUsd)) {
          spentUpperBoundUsd += record.usage.costUsd - maxCallUsd;
        }
        writeFileSync(join(out, 'calls.json'), `${JSON.stringify(calls, null, 2)}\n`);
      }
    },
  };
}

async function measurePhase(phases, key, fn) {
  const t0 = performance.now();
  try {
    return await fn();
  } finally {
    phases[key] = (phases[key] ?? 0) + (performance.now() - t0);
  }
}

async function runFawnTask({ repeat, spec, mode, inputs, workflowDir }) {
  const slug = spec.id.replace(/[^a-z0-9-]/g, '-');
  const workspaceId = `r${repeat}-${mode}-${slug}`;
  const runDir = join(out, `repeat-${repeat}`, workspaceId);
  mkdirSync(runDir, { recursive: true, mode: 0o700 });
  const started = performance.now();
  const phases = {};
  let adapter;
  let service;
  let invStore;
  let row;
  try {
    service = await measurePhase(phases, 'serviceOpenMs', () => WorkspaceService.open({
      stateDir: join(runDir, 'service'),
      config: serviceConfig,
      createAdapter: (options) => {
        adapter = createPlaywrightAdapter(options);
        return adapter;
      },
    }));
    const admin = { workspaceId, ...await service.createWorkspace({ workspaceId, scopedReads: true }) };
    await service.grantAuthorization({
      ...admin,
      grantId: 'ordinary-task',
      ownerId: 'agent',
      intents: ['ordinary-task'],
      actionKinds: ['navigate', 'fill', 'select', 'click'],
      targetOrigins: [server.origin],
      pageIds: ['main'],
      readRegions: null,
    });
    const owner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };
    const initialObs = await service.observe(owner);
    const startUrl = server.createSession(workspaceId, spec.routePath);
    const nav = await (await service.submitAction({
      ...owner,
      actionId: `nav-${workspaceId}`,
      authorizedIntent: 'ordinary-task',
      kind: 'navigate',
      target: { url: startUrl },
      observationVersion: initialObs.observationVersion,
    })).result;
    if (nav.outcome !== 'completed') throw Error(`Initial navigation failed: ${nav.outcome}`);

    const page = adapter._page(workspaceId, 'main');
    const initialPageState = spec.preparePage
      ? await measurePhase(phases, 'prepareMs', () => spec.preparePage(page))
      : null;

    invStore = new InvestigationStore(join(runDir, 'client'));
    invStore.create({ id: workspaceId, goal: spec.taskPrompt });
    const wfStore = new WorkflowStore({
      directory: workflowDir,
      ownerScope: `ordinary-repeat-${repeat}`,
      limits: { maxNodes: 128, maxEdges: 128, maxSteps: 24 },
      maxBytes: 4_000_000,
      lockWaitMs: 1000,
      lockRetryMs: 10,
    });

    const result = await measurePhase(phases, 'workflowRunMs', () => wfStore.run({
      mode,
      accountScope: 'ordinary-local-account',
      template: spec.template,
      verifyAccount: async () => (new URL(page.url()).origin === server.origin ? 'ordinary-local-account' : null),
      verificationId: `${spec.id}-oracle-v1`,
      taskSourceHashes: { runner: selfHash, site: siteHash },
      disclosurePolicy: {
        origin: server.origin,
        fields: spec.fields,
        intermediateClicks: spec.intermediateClicks,
      },
      learnRepairs: false,
      service,
      owner,
      pageId: 'main',
      intent: 'ordinary-task',
      inputs,
      task: spec.taskPrompt,
      planner: makePlanner(workspaceId, spec),
      config: { ...clientConfig, maxTurns: ceilings.maxTurnsPerRun },
      store: invStore,
      projectId: workspaceId,
      verifyReview: () => measurePhase(
        phases,
        'verificationMs',
        () => spec.verify(page, inputs, server, workspaceId, initialPageState),
      ),
      signal: new AbortController().signal,
    }));

    const oracle = await measurePhase(
      phases,
      'verificationMs',
      () => spec.verify(page, inputs, server, workspaceId, initialPageState),
    );
    const runCalls = calls.filter((c) => c.run === workspaceId);
    const measuredCostUsd = controlled
      ? 0
      : (runCalls.every((c) => Number.isFinite(c.usage?.costUsd))
          ? runCalls.reduce((sum, c) => sum + c.usage.costUsd, 0)
          : null);

    row = {
      repeat,
      taskId: spec.id,
      category: spec.category,
      arm: `fawn-${mode}`,
      mode,
      workspaceId,
      completed: Boolean(result.completed && oracle.completed),
      modelCalls: result.modelCalls,
      cacheSteps: result.cacheSteps,
      measuredCostUsd,
      phases,
      oracle,
      persistence: result.persistence,
      browserVersion: page.context().browser()?.version() ?? null,
      taskMs: 0,
    };
    return row;
  } catch (error) {
    row = {
      repeat,
      taskId: spec.id,
      category: spec.category,
      arm: `fawn-${mode}`,
      mode,
      workspaceId,
      completed: false,
      modelCalls: calls.filter((c) => c.run === workspaceId).length,
      cacheSteps: 0,
      measuredCostUsd: null,
      phases,
      error: error.message,
      taskMs: 0,
    };
    return row;
  } finally {
    invStore?.close();
    await measurePhase(phases, 'serviceCloseMs', () => service?.close());
    if (row) row.taskMs = performance.now() - started;
  }
}

async function runStockScriptFloor({ repeat, spec, inputs }) {
  const slug = spec.id.replace(/[^a-z0-9-]/g, '-');
  const sessionId = `r${repeat}-script-${slug}`;
  const profileDir = join(out, `repeat-${repeat}`, sessionId, 'profile');
  mkdirSync(profileDir, { recursive: true, mode: 0o700 });
  const started = performance.now();
  const phases = {};
  let context;
  let browser;
  let page;
  let row;
  try {
    context = await measurePhase(
      phases,
      'browserLaunchMs',
      () => chromium.launchPersistentContext(profileDir, { channel: 'chrome', headless: true }),
    );
    browser = context.browser();
    page = context.pages()[0] ?? await context.newPage();
    const startUrl = server.createSession(sessionId, spec.routePath);
    await measurePhase(phases, 'navigateMs', () => page.goto(startUrl, { waitUntil: 'load' }));
    const initialPageState = spec.preparePage
      ? await measurePhase(phases, 'prepareMs', () => spec.preparePage(page))
      : null;
    await measurePhase(phases, 'scriptActionsMs', () => spec.runStockScript(page, inputs));
    const oracle = await measurePhase(
      phases,
      'verificationMs',
      () => spec.verify(page, inputs, server, sessionId, initialPageState),
    );
    row = {
      repeat,
      taskId: spec.id,
      category: spec.category,
      arm: 'stock-script',
      mode: 'script',
      workspaceId: sessionId,
      completed: Boolean(oracle.completed),
      modelCalls: 0,
      cacheSteps: 0,
      measuredCostUsd: 0,
      phases,
      oracle,
      browserVersion: browser?.version() ?? null,
      taskMs: 0,
    };
    return row;
  } catch (error) {
    row = {
      repeat,
      taskId: spec.id,
      category: spec.category,
      arm: 'stock-script',
      mode: 'script',
      workspaceId: sessionId,
      completed: false,
      modelCalls: 0,
      cacheSteps: 0,
      measuredCostUsd: 0,
      phases,
      error: error.message,
      taskMs: 0,
    };
    return row;
  } finally {
    await measurePhase(phases, 'pageCloseMs', () => page?.close());
    await measurePhase(phases, 'contextCloseMs', () => context?.close());
    await measurePhase(phases, 'browserCloseMs', () => browser?.close());
    if (row) row.taskMs = performance.now() - started;
  }
}

function mean(values) {
  return values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0;
}

function stddev(values) {
  if (values.length < 2) return 0;
  const mu = mean(values);
  return Math.sqrt(values.reduce((s, v) => s + (v - mu) ** 2, 0) / (values.length - 1));
}

try {
  for (let repeat = 1; repeat <= repeats; repeat += 1) {
    const workflowDir = join(out, `repeat-${repeat}`, 'private-workflows');
    mkdirSync(workflowDir, { recursive: true, mode: 0o700 });

    for (let tIdx = 0; tIdx < specs.length; tIdx += 1) {
      const spec = specs[tIdx];
      const learnIn = spec.learnInputs[repeat - 1];
      const evalIn = spec.evalInputs[repeat - 1];

      const learnRow = await runFawnTask({ repeat, spec, mode: 'learn', inputs: learnIn, workflowDir });
      rows.push(learnRow);
      writeFileSync(join(out, 'rows.json'), `${JSON.stringify(rows, null, 2)}\n`);
      console.log(JSON.stringify({
        repeat,
        task: spec.id,
        arm: learnRow.arm,
        completed: learnRow.completed,
        seconds: Number((learnRow.taskMs / 1000).toFixed(3)),
        calls: learnRow.modelCalls,
        error: learnRow.error ?? null,
      }));

      // Alternate execution order between `fresh` and `reuse` on identical `evalIn`
      const pairModes = (repeat + tIdx) % 2 === 0 ? ['fresh', 'reuse'] : ['reuse', 'fresh'];
      for (const pairMode of pairModes) {
        const pairRow = await runFawnTask({ repeat, spec, mode: pairMode, inputs: evalIn, workflowDir });
        rows.push(pairRow);
        writeFileSync(join(out, 'rows.json'), `${JSON.stringify(rows, null, 2)}\n`);
        console.log(JSON.stringify({
          repeat,
          task: spec.id,
          arm: pairRow.arm,
          completed: pairRow.completed,
          seconds: Number((pairRow.taskMs / 1000).toFixed(3)),
          calls: pairRow.modelCalls,
          cacheSteps: pairRow.cacheSteps,
          error: pairRow.error ?? null,
        }));
      }

      const scriptRow = await runStockScriptFloor({ repeat, spec, inputs: evalIn });
      rows.push(scriptRow);
      writeFileSync(join(out, 'rows.json'), `${JSON.stringify(rows, null, 2)}\n`);
      console.log(JSON.stringify({
        repeat,
        task: spec.id,
        arm: scriptRow.arm,
        completed: scriptRow.completed,
        seconds: Number((scriptRow.taskMs / 1000).toFixed(3)),
        calls: 0,
        error: scriptRow.error ?? null,
      }));
    }
  }
} finally {
  await server.close();
}

const sourceUnchanged = Object.entries(sourceHashes).every(
  ([p, hash]) => sha256Hex(readFileSync(join(root, p))) === hash,
);
const rejectedWrites = server.getRejectedWrites();
const totalSubmissions = rows.reduce((sum, r) => sum + (r.oracle?.submissions ?? 0), 0);

const perRepeat = [];
for (let repeat = 1; repeat <= repeats; repeat += 1) {
  const rRows = rows.filter((r) => r.repeat === repeat);
  const summarize = (armName) => {
    const subset = rRows.filter((r) => r.arm === armName);
    const totalMs = subset.reduce((s, r) => s + r.taskMs, 0);
    return {
      runs: subset.length,
      correct: subset.filter((r) => r.completed).length,
      totalSeconds: Number((totalMs / 1000).toFixed(3)),
      totalMs,
      modelCalls: subset.reduce((s, r) => s + r.modelCalls, 0),
      cacheSteps: subset.reduce((s, r) => s + r.cacheSteps, 0),
      measuredCostUsd: subset.every((r) => Number.isFinite(r.measuredCostUsd))
        ? Number(subset.reduce((s, r) => s + r.measuredCostUsd, 0).toFixed(6))
        : null,
    };
  };
  const learn = summarize('fawn-learn');
  const fresh = summarize('fawn-fresh');
  const reuse = summarize('fawn-reuse');
  const script = summarize('stock-script');
  perRepeat.push({
    repeat,
    arms: { 'fawn-learn': learn, 'fawn-fresh': fresh, 'fawn-reuse': reuse, 'stock-script': script },
    reuseFasterThanFresh: reuse.totalMs < fresh.totalMs,
    secondsSavedReuseVsFresh: Number(((fresh.totalMs - reuse.totalMs) / 1000).toFixed(3)),
    speedupReuseVsFresh: reuse.totalMs > 0 ? Number((fresh.totalMs / reuse.totalMs).toFixed(2)) : null,
    callsSavedReuseVsFresh: fresh.modelCalls - reuse.modelCalls,
  });
}

const perTask = specs.map((spec) => {
  const tRows = rows.filter((r) => r.taskId === spec.id);
  const byArm = (armName) => {
    const subset = tRows.filter((r) => r.arm === armName);
    const secs = subset.map((r) => r.taskMs / 1000);
    const callCounts = subset.map((r) => r.modelCalls);
    return {
      runs: subset.length,
      correct: subset.filter((r) => r.completed).length,
      secondsByRepeat: secs.map((v) => Number(v.toFixed(3))),
      meanSeconds: Number(mean(secs).toFixed(3)),
      sdSeconds: Number(stddev(secs).toFixed(3)),
      callsByRepeat: callCounts,
      meanCalls: Number(mean(callCounts).toFixed(2)),
    };
  };
  const fresh = byArm('fawn-fresh');
  const reuse = byArm('fawn-reuse');
  const learn = byArm('fawn-learn');
  const script = byArm('stock-script');
  return {
    taskId: spec.id,
    category: spec.category,
    fresh,
    reuse,
    learn,
    stockScript: script,
    reuseWinsAllRepeats: fresh.secondsByRepeat.every((fSec, idx) => reuse.secondsByRepeat[idx] < fSec),
    meanSpeedupReuseVsFresh: reuse.meanSeconds > 0 ? Number((fresh.meanSeconds / reuse.meanSeconds).toFixed(2)) : null,
  };
});

const expectedRowCount = repeats * specs.length * 4;
const reuseRows = rows.filter((r) => r.arm === 'fawn-reuse');
const summary = {
  schema: 'fawn.ordinary-workflow-reuse-summary/v1',
  finishedAt: new Date().toISOString(),
  controlled,
  repeats,
  taskCount: specs.length,
  ceilings,
  totalModelCalls: calls.length,
  costUpperBoundUsd: Number(spentUpperBoundUsd.toFixed(6)),
  measuredTotalCostUsd: controlled
    ? 0
    : (calls.every((c) => Number.isFinite(c.usage?.costUsd))
        ? Number(calls.reduce((s, c) => s + c.usage.costUsd, 0).toFixed(6))
        : null),
  observedModels: [...new Set(calls.flatMap((c) => c.usage?.models ?? []))],
  browserVersions: [...new Set(rows.map((r) => r.browserVersion).filter(Boolean))],
  sourceUnchanged,
  rejectedSiteWrites: rejectedWrites,
  totalSubmissions,
  allRunsCompletedCorrectly: rows.length === expectedRowCount && rows.every((r) => r.completed),
  allReuseZeroModelCalls: reuseRows.length === repeats * specs.length && reuseRows.every((r) => r.modelCalls === 0),
  allRepeatsReuseFasterThanFresh: perRepeat.every((r) => r.reuseFasterThanFresh),
  perRepeat,
  perTask,
  aggregateAcrossRepeats: {
    freshMeanTotalSeconds: Number(mean(perRepeat.map((r) => r.arms['fawn-fresh'].totalSeconds)).toFixed(3)),
    freshSdTotalSeconds: Number(stddev(perRepeat.map((r) => r.arms['fawn-fresh'].totalSeconds)).toFixed(3)),
    reuseMeanTotalSeconds: Number(mean(perRepeat.map((r) => r.arms['fawn-reuse'].totalSeconds)).toFixed(3)),
    reuseSdTotalSeconds: Number(stddev(perRepeat.map((r) => r.arms['fawn-reuse'].totalSeconds)).toFixed(3)),
    learnMeanTotalSeconds: Number(mean(perRepeat.map((r) => r.arms['fawn-learn'].totalSeconds)).toFixed(3)),
    stockScriptMeanTotalSeconds: Number(mean(perRepeat.map((r) => r.arms['stock-script'].totalSeconds)).toFixed(3)),
    freshMeanTotalCalls: Number(mean(perRepeat.map((r) => r.arms['fawn-fresh'].modelCalls)).toFixed(2)),
    reuseMeanTotalCalls: Number(mean(perRepeat.map((r) => r.arms['fawn-reuse'].modelCalls)).toFixed(2)),
    learnMeanTotalCalls: Number(mean(perRepeat.map((r) => r.arms['fawn-learn'].modelCalls)).toFixed(2)),
  },
  productSuperiorityOverScriptEstablished: false,
  claim: 'Saved-workflow reuse completes all six ordinary tasks faster and with zero model calls compared with fresh planning after one verified learning run per repeat; a hand-written Playwright script remains faster on execution time with authoring effort unmeasured.',
};

writeFileSync(join(out, 'summary.json'), `${JSON.stringify(summary, null, 2)}\n`);
writeFileSync(join(out, 'assets.json'), `${JSON.stringify(server.assetHashes, null, 2)}\n`);
writeFileSync(join(out, 'rows.json'), `${JSON.stringify(rows, null, 2)}\n`);
console.log(JSON.stringify({ event: 'summary', summary: summary.aggregateAcrossRepeats, allRunsCompletedCorrectly: summary.allRunsCompletedCorrectly, allReuseZeroModelCalls: summary.allReuseZeroModelCalls }));

if (
  !summary.allRunsCompletedCorrectly
  || !summary.allReuseZeroModelCalls
  || !sourceUnchanged
  || rejectedWrites !== 0
  || totalSubmissions !== 0
) {
  process.exitCode = 1;
}
