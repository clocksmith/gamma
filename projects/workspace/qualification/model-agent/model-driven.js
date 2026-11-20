// Fawn workspace model-driven comparison runner (entered through differentiate.js).
//
// Modes:
// - compatibility: one request with the frozen model, system prompt, tools and thinking setting
// - smoke: the frozen wiring smoke (development clean scenarios only, never held-out)
// - full: every frozen scenario once, interleaving both arms per repetition
// - offline: the scripted stand-in model (scripted-model.js) on any scenarios, without any API call
// Every billed request is charged to one ledger shared across modes, under the approved ceiling.

import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { Checkpoint } from '../agents/checkpoint.js';
import { AGENT_ACTION_KINDS, AGENT_RESTART_DELAY_MS, Arm, HUMAN_HOLD_FACTOR, median, sleep, until } from '../arms.js';
import { REPO_ROOT, gitState, resultIdentity } from '../identity.js';
import { runModelTask } from './agent-loop.js';
import { ProviderError, createClient } from './anthropic-client.js';
import { APPS } from './apps.js';
import { FawnModelBackend, PlaywrightModelBackend } from './backends.js';
import { createScriptedClient } from './scripted-model.js';
import { SpendLedger } from './spend-ledger.js';

const POLICY_PATH = 'projects/workspace/config/browser-product-comparison-policy.json';
const OUT_ROOT = 'bench/out/fawn-model-driven';
const LEDGER_FILE = 'spend-ledger.json';
const FULL_RUN_MARKER = 'full-run-started.json';
const COMPATIBILITY_FILE = 'compatibility.json';
const SMOKE_FILE = 'smoke.json';
const KEY_FILE = join(homedir(), '.config/anthropic/api-key');
const KEY_FILE_SHARED_BITS = 0o077;
const ARMS = Object.freeze(['treatment', 'control']);
// The frozen fill tool also sets select controls, so the treatment's grant covers select.
const MODEL_ACTION_KINDS = Object.freeze([...AGENT_ACTION_KINDS, 'select']);
const HUMAN_TYPE_LIMIT_MS = 10000;
const COMPATIBILITY_PROMPT = 'Reply with the single word ready, without calling any tool.';
const HELD_OUT_APPS = Object.freeze({ 'clinic-booking': 'clinic-booking', 'expense-filing': 'expense-filing' });

const sha256 = (path) => createHash('sha256').update(readFileSync(join(REPO_ROOT, path))).digest('hex');
const fillTemplate = (template, values) => template.replace(/\{(\w+)\}/g, (_, key) => {
  if (!(key in values)) throw new Error(`task prompt needs ${key}`);
  return values[key];
});

function loadFrozen(suite) {
  for (const artifact of suite.frozenArtifacts) {
    if (sha256(artifact.path) !== artifact.sha256) throw new Error(`${artifact.path} differs from its frozen hash`);
  }
  const read = (name) => readFileSync(join(REPO_ROOT, 'projects/workspace/qualification/model-agent', name), 'utf8');
  return {
    system: read('system-prompt.md'),
    tools: JSON.parse(read('tools.json')).tools,
    taskPrompts: JSON.parse(read('task-prompts.json')).tasks,
    heldOut: JSON.parse(read('held-out-workflows.json')).workflows,
  };
}

function buildScenarios(comparison, frozen) {
  const development = [
    ...comparison.differentiation.scenarios.map((scenario) => ({ ...scenario, app: 'procurement' })),
    ...comparison.revalidatedDifferentiation.scenarios.map((scenario) => ({ ...scenario, app: 'helpdesk' })),
  ];
  const heldOut = Object.entries(frozen.heldOut).flatMap(([app, workflow]) => workflow.scenarios.map((scenario) => ({
    ...scenario,
    app: HELD_OUT_APPS[app],
    heldOut: true,
    inputs: workflow.inputs,
    application: scenario.area === 'interruption-recovery' ? 'interrupted' : 'default',
  })));
  return [...development, ...heldOut];
}

// The key never reaches child processes (service host, tool host, browsers), receipts or logs.
let secret = null;

function readApiKey(fromEnvironment) {
  if (fromEnvironment) return fromEnvironment;
  if (!existsSync(KEY_FILE)) return null;
  if (statSync(KEY_FILE).mode & KEY_FILE_SHARED_BITS) throw new Error(`${KEY_FILE} must be readable only by its owner (chmod 600)`);
  return readFileSync(KEY_FILE, 'utf8').trim();
}

function guarded(text, where) {
  if (secret && text.includes(secret)) throw new Error(`refusing to write ${where}: it contains the API key`);
  return text;
}

const writeReceipt = (path, value) => writeFileSync(path, guarded(typeof value === 'string' ? value : `${JSON.stringify(value, null, 2)}\n`, path));
const log = (line) => console.log(guarded(line, 'the log'));

/** Each application fixture's current hash against the hash bound after implementation. */
function fixtureIdentity(suite) {
  return suite.fixtureSites.sites.map((site) => {
    const current = sha256(site.path);
    return { ...site, current, matches: current === site.sha256 };
  });
}

async function runModelArm({ name, scenario, repetition, frozen, suite, client, ledger, mode, humanHoldMs }) {
  const app = APPS[scenario.app];
  const site = await app.startSite();
  const application = app.applications[scenario.application ?? app.defaultApplication];
  const flags = { ...application, churn: scenario.area === 'incremental-observation' };
  await fetch(`${site.origin}/control/setup?${new URLSearchParams(Object.entries(flags).map(([key, value]) => [key, value ? '1' : '0']))}`);
  const arm = new Arm({ name, site, scenario, definition: { intent: app.intent, humanFill: app.humanFill, actionKinds: MODEL_ACTION_KINDS, profiles: {}, controlOptions: {} } });
  await arm.start();
  const id = `${scenario.id}-${name}-${repetition}`;
  const inputs = { origin: site.origin, ...app.inputs(site, id), ...(scenario.inputs ?? {}) };
  const taskPrompt = fillTemplate(frozen.taskPrompts[scenario.app], inputs);
  const task = { id, intent: app.intent, origin: site.origin, incarnation: 1 };
  const conversation = new Checkpoint(join(arm.root, 'conversation.json'));
  const harness = new Checkpoint(join(arm.root, 'harness.json'));
  const humanWindow = {};
  const perturbState = {};
  // The person takes the browser and types while the model's action is in flight, as in the
  // development suites; the action waits only until the person has typed.
  let humanSequence = null;
  const startHumanControl = async () => {
    humanSequence = arm.humanTakesControl(humanWindow, humanHoldMs);
    await until(() => site.state.mutations.some((entry) => entry.kind === 'human-fill'), HUMAN_TYPE_LIMIT_MS, 'the person to type');
  };
  const hooks = { beforeAction: ({ tool, target }) => app.perturb({ site, scenario, tool, target, state: perturbState, startHumanControl }) };
  const backendFor = () => (name === 'treatment'
    ? new FawnModelBackend({ host: arm.host, identity: { current: () => arm.owner }, task, hooks })
    : new PlaywrightModelBackend({ host: arm.host, pause: arm.pause, task, checkpoint: harness, hooks }));
  let alive = true;
  const observations = [];
  // Provider failures and the spend ceiling stop the suite; they are not task outcomes.
  let suiteStop = null;
  const settle = (promise) => promise.then((result) => ({ result, error: null }), (error) => {
    if (error instanceof ProviderError || error.code === 'spend-ceiling') suiteStop ??= error;
    return { result: null, error: { code: error.code ?? null, message: error.message } };
  });
  let backend = null;
  const run = () => {
    backend = backendFor();
    return runModelTask({
      client, frozen: { system: frozen.system, tools: frozen.tools, taskPrompt }, agent: suite.agent, backend,
      checkpoint: conversation, alive: () => alive, observations, purpose: `${mode}:${id}:${task.incarnation}`,
    });
  };
  const started = performance.now();
  let outcome;
  let restarted = false;
  if (scenario.area === 'interruption-recovery') {
    const held = site.hold(app.holdTarget);
    const running = settle(run());
    const first = await Promise.race([held.reached.then(() => 'held'), running.then(() => 'finished')]);
    if (first === 'held') {
      alive = false;
      backend.kill();
      held.release();
      await running;
      await sleep(AGENT_RESTART_DELAY_MS);
      alive = true;
      task.incarnation += 1;
      restarted = true;
      outcome = await settle(run());
    } else {
      outcome = await running;
    }
  } else {
    outcome = await settle(run());
  }
  const completeTaskLatencyMs = performance.now() - started;
  await humanSequence;
  arm.inspect();
  if (suiteStop) {
    await arm.close();
    await site.close();
    throw suiteStop;
  }
  const verdict = app.judge(site, app.judgeTask(site, id), scenario, outcome, humanWindow, inputs);
  const usage = conversation.get();
  let observationTokens = 0;
  for (const text of observations) observationTokens += await client.countTokens(text);
  const row = {
    scenarioId: scenario.id,
    app: scenario.app,
    heldOut: Boolean(scenario.heldOut),
    arm: name,
    repetition,
    ...verdict,
    incorrectExternalEffects: verdict.incorrectActions,
    duplicates: verdict[app.duplicateField] ?? verdict.duplicateEffects ?? 0,
    recovery: scenario.area === 'interruption-recovery' ? restarted && verdict.taskSuccess : null,
    observationBytes: observations.reduce((total, text) => total + Buffer.byteLength(text), 0),
    observationTokens,
    inputTokens: usage.inputTokens ?? 0,
    outputTokens: usage.outputTokens ?? 0,
    inferenceCostUsd: ledger ? ledger.cost(usage.inputTokens ?? 0, usage.outputTokens ?? 0) : 0,
    turns: usage.turns ?? 0,
    completeTaskLatencyMs,
  };
  const evidence = { scenarioId: scenario.id, arm: name, repetition, transcript: usage.messages ?? [], fixture: site.state.mutations };
  await arm.close();
  await site.close();
  return { row, evidence, inspections: arm.inspections };
}

const sum = (rows, field) => rows.reduce((total, row) => total + (row[field] ?? 0), 0);
const rate = (rows) => (rows.length ? rows.filter((row) => row.taskSuccess).length / rows.length : 0);

const BARS = Object.freeze({
  minimumSuccessRate: (t, c, value) => rate(t) >= value,
  incorrectExternalEffects: (t, c, value) => sum(t, 'incorrectExternalEffects') === value,
  humanReviews: (t, c, value) => sum(t, 'humanReviews') === value,
  successRateNotBelowControl: (t, c) => rate(t) >= rate(c),
  maximumSuccessRateBelowControl: (t, c, value) => rate(t) >= rate(c) - value,
  incorrectExternalEffectsNotAboveControl: (t, c) => sum(t, 'incorrectExternalEffects') <= sum(c, 'incorrectExternalEffects'),
});

function evaluate(rows, suite, comparison, isFull) {
  const requirements = suite.improvementRequirements.map((requirement) => {
    const pick = (arm) => rows.filter((row) => requirement.scenarios.includes(row.scenarioId) && row.arm === arm);
    const treatment = pick('treatment');
    const control = pick('control');
    if (!treatment.length) return { area: requirement.area, status: 'not-run' };
    const bar = Object.entries(requirement.treatmentBar).map(([field, value]) => ({ field, value, met: BARS[field](treatment, control, value) }));
    let improvement = null;
    if (requirement.kind === 'advantage') {
      const { measure } = requirement.materialImprovement;
      if (measure === 'observationTokens') {
        const ratio = median(treatment.map((row) => row.observationTokens)) / median(control.map((row) => row.observationTokens));
        const cost = { treatment: sum(treatment, 'inferenceCostUsd'), control: sum(control, 'inferenceCostUsd') };
        improvement = { measure, ratio, cost, met: ratio <= requirement.materialImprovement.maximumTreatmentToControlRatio && cost.treatment < cost.control };
      } else {
        const value = (subset) => sum(subset, 'humanReviews') + sum(subset, 'duplicates');
        improvement = { measure, treatment: value(treatment), control: value(control), met: value(treatment) < value(control) };
      }
    }
    const met = bar.every((entry) => entry.met) && (improvement === null || improvement.met);
    return { area: requirement.area, kind: requirement.kind, status: met ? 'met' : 'not-met', bar, improvement,
      successRate: { treatment: rate(treatment), control: rate(control) } };
  });
  const rule = suite.productAdvantageRule;
  const latency = comparison.criteria.latency;
  const latencyRegressions = [...new Set(rows.map((row) => row.scenarioId))].filter((scenarioId) => {
    const of = (arm) => median(rows.filter((row) => row.scenarioId === scenarioId && row.arm === arm).map((row) => row.completeTaskLatencyMs));
    const [t, c] = [of('treatment'), of('control')];
    return t > c * latency.regressionRatio && t - c > latency.minimumDeltaMs;
  });
  const costRatio = sum(rows.filter((row) => row.arm === 'treatment'), 'inferenceCostUsd')
    / Math.max(sum(rows.filter((row) => row.arm === 'control'), 'inferenceCostUsd'), Number.EPSILON);
  const status = (area) => requirements.find((entry) => entry.area === area)?.status;
  return {
    requirements,
    productAdvantage: {
      areasMet: rule.requiresAreasMet.filter((area) => status(area) === 'met'),
      nonInferiorityMet: rule.requiresNonInferiority.filter((area) => status(area) === 'met'),
      latencyRegressions,
      totalInferenceCostRatio: costRatio,
      established: isFull && rule.requiresAreasMet.every((area) => status(area) === 'met')
        && rule.requiresNonInferiority.every((area) => status(area) === 'met')
        && latencyRegressions.length === 0 && costRatio <= rule.maximumTotalInferenceCostRatio,
      doesNotEstablish: rule.doesNotEstablish,
    },
  };
}

async function runModelDriven(options) {
  const comparison = JSON.parse(readFileSync(join(REPO_ROOT, POLICY_PATH), 'utf8')).workspaceComparison;
  const suite = comparison.modelDrivenDifferentiation;
  const frozen = loadFrozen(suite);
  const mode = options.mode ?? 'full';
  const environmentKey = process.env.ANTHROPIC_API_KEY;
  delete process.env.ANTHROPIC_API_KEY;
  const fixtures = fixtureIdentity(suite);
  const fixturesMatchFrozen = fixtures.every((site) => site.matches);
  const stamp = new Date().toISOString().replace(/[:.]/g, '').slice(0, 15);
  const outDir = options.out ?? join(REPO_ROOT, OUT_ROOT, `${mode}-${stamp}Z`);
  const ledgerDir = join(REPO_ROOT, OUT_ROOT);
  mkdirSync(ledgerDir, { recursive: true });
  let client;
  let ledger = null;
  if (mode === 'offline') {
    client = createScriptedClient();
  } else {
    const apiKey = readApiKey(environmentKey);
    if (!apiKey) throw new Error(`model API credentials are required: set ANTHROPIC_API_KEY or write ${KEY_FILE} (mode 0600)`);
    secret = apiKey;
    ledger = new SpendLedger({ path: join(ledgerDir, LEDGER_FILE), ceilingUsd: suite.spend.approvedCeilingUsd, prices: suite.spend.pricesPerMillionTokensUsd });
    client = createClient({ apiKey, agent: suite.agent, ledger });
  }
  const git = gitState();
  if (mode !== 'offline') {
    const changes = git.workingTreeChanges ?? ['unknown'];
    if (changes.length) throw new Error(`billed runs need committed source; uncommitted: ${changes.join('; ')}`);
  }
  if (mode === 'compatibility') {
    const response = await client.turn({ system: frozen.system, tools: frozen.tools,
      messages: [{ role: 'user', content: COMPATIBILITY_PROMPT }], purpose: 'compatibility' });
    const record = { model: response.model, stopReason: response.stop_reason, usage: response.usage,
      contentTypes: response.content.map((block) => block.type), request: { model: suite.agent.model, thinking: suite.agent.thinking, samplingParameters: suite.agent.samplingParameters },
      passed: response.model?.startsWith(suite.agent.model) && !response.content.some((block) => block.type === 'thinking'),
      sourceCommit: git.commit, spentUsd: ledger.spentUsd };
    writeReceipt(join(ledgerDir, COMPATIBILITY_FILE), record);
    log(JSON.stringify(record));
    return;
  }
  const passed = (file) => existsSync(join(ledgerDir, file)) && JSON.parse(readFileSync(join(ledgerDir, file), 'utf8')).passed === true;
  if (mode === 'smoke' || mode === 'full') {
    if (!passed(COMPATIBILITY_FILE)) throw new Error('the compatibility request has not passed');
    const changed = fixtures.filter((site) => !site.matches).map((site) => site.path);
    if (changed.length) throw new Error(`fixtures differ from their bound hashes: ${changed.join(', ')}`);
  }
  if (mode === 'full') {
    if (!passed(SMOKE_FILE)) throw new Error('the wiring smoke has not completed');
    if (existsSync(join(ledgerDir, FULL_RUN_MARKER))) throw new Error('the full suite has already been started once');
    writeReceipt(join(ledgerDir, FULL_RUN_MARKER), { startedAt: new Date().toISOString(), outDir });
  }
  mkdirSync(outDir, { recursive: true });
  const all = buildScenarios(comparison, frozen);
  const SCOPES = {
    offline: { scenarios: options.scenarios ?? suite.wiringSmoke.scenarios, repetitions: 1 },
    smoke: { scenarios: suite.wiringSmoke.scenarios, repetitions: suite.wiringSmoke.repetitions },
    full: { scenarios: all.map((scenario) => scenario.id), repetitions: suite.repetitions },
  };
  const scope = SCOPES[mode];
  const scenarios = all.filter((scenario) => scope.scenarios.includes(scenario.id));
  if (mode === 'smoke' && scenarios.some((scenario) => scenario.heldOut)) throw new Error('the model runs held-out scenarios only in the full suite');
  const humanHoldMs = comparison.revalidatedDifferentiation.thinkTimeMs * HUMAN_HOLD_FACTOR;
  const rows = [];
  const evidence = [];
  const executables = new Map();
  let stopped = null;
  outer: for (const scenario of scenarios) {
    for (let repetition = 1; repetition <= scope.repetitions; repetition += 1) {
      for (const name of repetition % 2 ? ARMS : [...ARMS].reverse()) {
        try {
          const run = await runModelArm({ name, scenario, repetition, frozen, suite, client, ledger, mode, humanHoldMs });
          rows.push(run.row);
          evidence.push(run.evidence);
          for (const inspection of run.inspections) for (const executable of inspection.executables) executables.set(executable.sha256, executable);
          if ([...executables.keys()].some((sha256) => sha256 !== suite.browserBinary.sha256)) {
            stopped = 'the browser binary differs from the frozen binary';
            break outer;
          }
          log(`ran: ${scenario.id} ${name} ${repetition}: ${run.row.taskSuccess ? 'success' : 'failure'} (${run.row.details.status})`
            + ` incorrect ${run.row.incorrectExternalEffects} reviews ${run.row.humanReviews} obs-tokens ${run.row.observationTokens}`
            + ` cost ${run.row.inferenceCostUsd.toFixed(3)} spent ${ledger ? ledger.spentUsd.toFixed(2) : 'offline'}`);
        } catch (error) {
          stopped = `${scenario.id} ${name} ${repetition}: ${error.message}`;
          break outer;
        }
      }
    }
  }
  const isFull = mode === 'full' && !stopped;
  const evaluation = evaluate(rows, suite, comparison, isFull);
  const browsers = [...executables.values()];
  const result = {
    schemaVersion: 1,
    suiteVersion: suite.suiteVersion,
    mode,
    scope: isFull ? 'full' : (mode === 'full' ? 'stopped' : mode),
    stopped,
    identity: resultIdentity(),
    fixtureSites: fixtures,
    fixturesMatchFrozen,
    knownRepresentationDifferences: suite.knownRepresentationDifferences,
    agent: suite.agent,
    browsers,
    sameFrozenBrowser: browsers.length === 1 && browsers[0].sha256 === suite.browserBinary.sha256,
    spentUsd: ledger?.spentUsd ?? 0,
    ...evaluation,
    rows,
  };
  writeReceipt(join(outDir, 'model-driven.json'), result);
  if (mode === 'smoke') {
    writeReceipt(join(ledgerDir, SMOKE_FILE), { passed: !stopped && result.sameFrozenBrowser && fixturesMatchFrozen, stopped, result: join(outDir, 'model-driven.json') });
  }
  writeReceipt(join(outDir, 'transcripts.json'), `${JSON.stringify(evidence)}\n`);
  for (const requirement of evaluation.requirements) log(`${requirement.area}: ${requirement.status}`);
  if (stopped) log(`stopped: ${stopped}`);
  log(`product advantage established: ${evaluation.productAdvantage.established}; spent ${result.spentUsd.toFixed(2)}; ${join(outDir, 'model-driven.json')}`);
  if (stopped) process.exitCode = 1;
}

export { buildScenarios, runModelDriven };
