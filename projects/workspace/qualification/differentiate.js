#!/usr/bin/env node
// Fawn workspace differentiation runner.
//
// Runs the frozen scenarios of one suite in workspaceComparison of
// projects/workspace/config/browser-product-comparison-policy.json (differentiation-suites.js names each suite's
// application side). The treatment agent is a client of the workspace
// service; the control agent uses Playwright agent tooling. Both run the same policy and think
// time against a fresh workbench site per run, interleaved per repetition. The workbench's own
// orders, cart and mutation log judge every run; the frozen requirements decide each area.
//
// Usage: node qualification/differentiate.js [--suite differentiation|revalidatedDifferentiation|engineeringInvestigation]
//   [--out DIR] [--scenarios id,id] [--repetitions n] [--scripted-comparison comparison.json]
//   [--prior-suites differentiation.json,...]
//   --suite modelDrivenDifferentiation --mode compatibility|smoke|full|offline runs the model-driven suite

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { AGENT_RESTART_DELAY_MS, Arm, HUMAN_HOLD_FACTOR, median, sleep } from './arms.js';
import { SUITES } from './differentiation-suites.js';
import { REPO_ROOT, executableIdentityKey, resultIdentity } from './identity.js';
import { stageBrowserProfile, matchesSelectedBuild } from './browser-profile.js';
import { loadServiceConfig } from '../src/config.js';

const POLICY_PATH = 'projects/workspace/config/browser-product-comparison-policy.json';
const DEFAULT_OUT_ROOT = 'bench/out/fawn-workspace-differentiation';
const DIFFERENTIATION_SCHEMA_VERSION = 1;
const ARMS = Object.freeze(['treatment', 'control']);
const WORKSPACE_ROOT = fileURLToPath(new URL('../', import.meta.url));
// Agent-side code each arm needs beyond the shared policy and the application profile.
const HARNESS_FILES = Object.freeze({
  treatment: ['qualification/agents/fawn-agent.js'],
  control: ['qualification/agents/playwright-agent.js', 'qualification/agents/playwright-tool-host.js'],
});

function codeLines(relativePath) {
  return readFileSync(join(WORKSPACE_ROOT, relativePath), 'utf8').split('\n').map((line) => line.trim())
    .filter((line) => line && !line.startsWith('//') && !line.startsWith('*') && !line.startsWith('/*')).length;
}

function parseArgs(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 2) options[argv[index].replace(/^--/, '')] = argv[index + 1];
  return {
    out: options.out ?? null,
    scenarios: options.scenarios ? options.scenarios.split(',') : null,
    repetitions: options.repetitions ? Number(options.repetitions) : null,
    scriptedComparison: options['scripted-comparison'] ?? null,
    suite: options.suite ?? 'differentiation',
    mode: options.mode ?? null,
    browserChannel: options['browser-channel'] ?? null,
    browserConfig: options['browser-config'] ?? null,
    priorSuites: options['prior-suites'] ? options['prior-suites'].split(',') : [],
  };
}

async function runArm(name, scenario, repetition, suite, definition, browserChannel, browserConfig) {
  const site = await definition.startSite();
  const application = definition.applications[scenario.application ?? definition.defaultApplication];
  const flags = { ...application, churn: scenario.area === 'incremental-observation' };
  await fetch(`${site.origin}/control/setup?${new URLSearchParams(Object.entries(flags).map(([key, value]) => [key, value ? '1' : '0']))}`);
  const arm = new Arm({ name, site, scenario, definition, browserChannel, browserConfig });
  await arm.start();
  const id = `${scenario.id}-${name}-${repetition}`;
  const task = { id, intent: definition.intent, origin: site.origin, ...definition.task(site, id) };
  const humanWindow = {};
  let humanSequence = null;
  const startHumanControl = () => {
    humanSequence ??= arm.humanTakesControl(humanWindow, suite.thinkTimeMs * HUMAN_HOLD_FACTOR);
  };
  const hooks = { decision: (stage, info) => definition.perturb({ site, scenario, stage, info, startHumanControl }) };
  const started = performance.now();
  let incarnation = 1;
  let agent = arm.createAgent(task, suite.thinkTimeMs, incarnation);
  let observationBytes = 0;
  const settle = (promise) => promise.then((result) => ({ result, error: null }), (error) => ({ result: null, error: { code: error.code ?? null, message: error.message } }));
  let outcome;
  if (scenario.area === 'interruption-recovery') {
    const held = site.hold(definition.holdTarget);
    const running = settle(definition.policy(agent, task, hooks));
    const first = await Promise.race([held.reached.then(() => 'held'), running.then(() => 'finished')]);
    if (first === 'held') {
      agent.kill();
      held.release();
      await running;
      observationBytes += agent.observationBytes;
      await sleep(AGENT_RESTART_DELAY_MS);
      incarnation += 1;
      agent = arm.createAgent(task, suite.thinkTimeMs, incarnation);
      outcome = await settle(definition.policy(agent, task, hooks));
    } else {
      outcome = await running;
    }
  } else {
    outcome = await settle(definition.policy(agent, task, hooks));
  }
  await humanSequence;
  observationBytes += agent.observationBytes;
  const latencyMs = performance.now() - started;
  arm.inspect();
  const verdict = definition.judge(site, task, scenario, outcome, humanWindow);
  const evidence = { requests: site.state.requests.length, ...definition.evidence(site) };
  await arm.close();
  await site.close();
  return {
    row: { scenarioId: scenario.id, arm: name, repetition, ...verdict, observationBytes, latencyMs, agentIncarnations: incarnation },
    inspections: arm.inspections,
    evidence,
  };
}

const sum = (rows, field) => rows.reduce((total, row) => total + row[field], 0);
const MEASURES = Object.freeze({
  humanReviewsPlusDuplicateOrders: (rows) => sum(rows, 'humanReviews') + sum(rows, 'duplicateOrders'),
  humanReviewsPlusDuplicateEffects: (rows) => sum(rows, 'humanReviews') + sum(rows, 'duplicateEffects'),
});

function measureOf(rows, measure) {
  return MEASURES[measure] ? MEASURES[measure](rows) : sum(rows, measure);
}

function checkBar(rows, bar) {
  return Object.entries(bar).map(([field, expected]) => {
    if (field === 'taskSuccessEveryRepetition') return { field, expected, observed: rows.every((row) => row.taskSuccess), met: rows.every((row) => row.taskSuccess) === expected };
    const observed = sum(rows, field);
    return { field, expected, observed, met: observed === expected };
  });
}

function evaluateRequirement(requirement, rows) {
  const treatment = rows.filter((row) => row.scenarioId === requirement.scenario && row.arm === 'treatment');
  const control = rows.filter((row) => row.scenarioId === requirement.scenario && row.arm === 'control');
  if (treatment.length === 0) return { ...requirement, status: 'not-run' };
  const bar = checkBar(treatment, requirement.treatmentBar);
  const { measure } = requirement.materialImprovement;
  let improvement;
  if (requirement.materialImprovement.maximumTreatmentToControlRatio !== undefined) {
    const ratio = median(treatment.map((row) => row[measure])) / median(control.map((row) => row[measure]));
    improvement = { measure, ratio, maximum: requirement.materialImprovement.maximumTreatmentToControlRatio, met: ratio <= requirement.materialImprovement.maximumTreatmentToControlRatio };
  } else {
    const observed = { treatment: measureOf(treatment, measure), control: measureOf(control, measure) };
    improvement = { measure, ...observed, met: observed.treatment < observed.control };
  }
  const met = bar.every((entry) => entry.met) && improvement.met;
  return { area: requirement.area, scenario: requirement.scenario, status: met ? 'met' : 'not-met', bar, improvement };
}

/** A regression is any scenario where the treatment is materially worse on a decisive measure. */
function regressions(rows, scenarios, latencyRule, duplicateField) {
  const found = [];
  for (const scenario of scenarios) {
    const treatment = rows.filter((row) => row.scenarioId === scenario.id && row.arm === 'treatment');
    const control = rows.filter((row) => row.scenarioId === scenario.id && row.arm === 'control');
    if (treatment.length === 0) continue;
    const successes = (subset) => subset.filter((row) => row.taskSuccess).length;
    if (successes(treatment) < successes(control)) found.push({ scenario: scenario.id, measure: 'taskSuccess' });
    for (const measure of ['incorrectActions', 'humanReviews', duplicateField, 'mutationsDuringHumanControl']) {
      if (sum(treatment, measure) > sum(control, measure)) found.push({ scenario: scenario.id, measure });
    }
    const latency = { treatment: median(treatment.map((row) => row.latencyMs)), control: median(control.map((row) => row.latencyMs)) };
    if (latency.treatment > latency.control * latencyRule.regressionRatio && latency.treatment - latency.control > latencyRule.minimumDeltaMs) {
      found.push({ scenario: scenario.id, measure: 'completeTaskLatencyMs', ...latency });
    }
  }
  return found;
}

function scenarioSummary(rows, scenario, duplicateField) {
  const pick = (arm) => rows.filter((row) => row.scenarioId === scenario.id && row.arm === arm);
  return Object.fromEntries(ARMS.map((arm) => {
    const subset = pick(arm);
    return [arm, {
      successes: subset.filter((row) => row.taskSuccess).length,
      repetitions: subset.length,
      incorrectActions: sum(subset, 'incorrectActions'),
      constraintViolatingMutations: sum(subset, 'constraintViolatingMutations'),
      humanReviews: sum(subset, 'humanReviews'),
      [duplicateField]: sum(subset, duplicateField),
      mutationsDuringHumanControl: sum(subset, 'mutationsDuringHumanControl'),
      medianObservationBytes: median(subset.map((row) => row.observationBytes)),
      medianLatencyMs: median(subset.map((row) => row.latencyMs)),
    }];
  }));
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.suite === 'modelDrivenDifferentiation') {
    if (options.browserConfig || options.browserChannel) throw new Error('model-driven suite retains its frozen browser selection');
    const { runModelDriven } = await import('./model-agent/model-driven.js');
    await runModelDriven(options);
    process.exit(process.exitCode ?? 0);
  }
  const comparison = JSON.parse(readFileSync(join(REPO_ROOT, POLICY_PATH), 'utf8')).workspaceComparison;
  const definition = SUITES[options.suite];
  const suite = comparison[options.suite] ?? definition?.suiteConfig;
  if (!suite || !definition) throw new Error(`unknown suite ${options.suite}`);
  const stamp = new Date().toISOString().replace(/[:.]/g, '').slice(0, 15);
  const outDir = options.out ?? join(REPO_ROOT, DEFAULT_OUT_ROOT, `${stamp}Z`);
  mkdirSync(outDir, { recursive: true });
  if (options.browserConfig && options.browserChannel) throw new Error('choose browser config or channel');
  const profile = stageBrowserProfile(options.browserConfig, outDir);
  if (profile && !profile.config.browser.headless) throw new Error('profile must preserve frozen differentiation headless mode');
  loadServiceConfig(profile?.path ?? undefined, { browserChannel: options.browserChannel });
  const identity = resultIdentity();
  if (profile) identity.browserLaunchConfig = profile.identity;
  const scenarios = suite.scenarios.filter((scenario) => !options.scenarios || options.scenarios.includes(scenario.id));
  const rows = [];
  const inspections = { treatment: [], control: [] };
  const evidence = [];
  for (const scenario of scenarios) {
    const repetitions = options.repetitions ?? scenario.repetitions;
    for (let repetition = 1; repetition <= repetitions; repetition += 1) {
      for (const name of repetition % 2 ? ARMS : [...ARMS].reverse()) {
        const run = await runArm(name, scenario, repetition, suite, definition, options.browserChannel, profile?.path);
        rows.push(run.row);
        inspections[name].push(...run.inspections);
        evidence.push({ scenarioId: scenario.id, arm: name, repetition, ...run.evidence });
        console.log(`ran: ${scenario.id} ${name} ${repetition}: ${run.row.taskSuccess ? 'success' : 'failure'}`
          + ` incorrect ${run.row.incorrectActions} reviews ${run.row.humanReviews} bytes ${run.row.observationBytes}`
          + ` ${Math.round(run.row.latencyMs)} ms${run.row.details.error ? ` (${run.row.details.error.message})` : ''}`);
      }
    }
  }
  const requirements = suite.improvementRequirements.map((requirement) => evaluateRequirement(requirement, rows));
  const suiteRegressions = regressions(rows, scenarios, comparison.criteria.latency, definition.duplicateField);
  let scriptedRegressions = null;
  if (options.scriptedComparison) {
    const scripted = JSON.parse(readFileSync(options.scriptedComparison, 'utf8'));
    scriptedRegressions = scripted.evaluation.flatMap((entry) => entry.findings.filter((finding) => finding.direction === 'regression')
      .map((finding) => ({ scenario: entry.scenarioId, measure: finding.measure })));
  }
  // Earlier frozen suites named by the rule must have run in full without regression.
  const priorRegressions = options.priorSuites.map((path) => {
    const prior = JSON.parse(readFileSync(path, 'utf8'));
    return { path, suiteVersion: prior.suiteVersion, full: prior.scope === 'full', regressions: prior.productAdvantage.suiteRegressions };
  });
  const priorsClean = priorRegressions.every((prior) => prior.full && prior.regressions.length === 0);
  const rule = suite.productAdvantageRule;
  const priorsRequired = rule.noMaterialRegressionIn.length - 2;
  const areasMet = requirements.filter((requirement) => requirement.status === 'met').map((requirement) => requirement.area);
  const isFull = !options.scenarios && !options.repetitions;
  const productAdvantage = {
    areasMet,
    suiteRegressions,
    scriptedRegressions,
    priorRegressions,
    established: isFull && areasMet.length >= rule.minimumAreasMet && suiteRegressions.length === 0
      && Array.isArray(scriptedRegressions) && scriptedRegressions.length === 0
      && priorRegressions.length >= priorsRequired && priorsClean,
    doesNotEstablish: rule.doesNotEstablish,
  };
  const executables = Object.fromEntries(ARMS.map((name) => [name, [...new Map(inspections[name].flatMap((inspection) => inspection.executables)
    .map((executable) => [executableIdentityKey(executable), executable])).values()]]));
  const sameBrowserBinary = executables.treatment.length === 1 && executables.control.length === 1
    && executableIdentityKey(executables.treatment[0]) === executableIdentityKey(executables.control[0])
    && matchesSelectedBuild(profile?.config, executables.treatment);
  const debuggingEndpoints = [...inspections.treatment, ...inspections.control]
    .reduce((total, inspection) => total + inspection.listeningTcpSockets + inspection.devToolsActivePortFiles, 0);
  productAdvantage.established &&= sameBrowserBinary && debuggingEndpoints === 0;
  const result = {
    schemaVersion: DIFFERENTIATION_SCHEMA_VERSION,
    suiteVersion: suite.suiteVersion,
    scope: isFull ? 'full' : 'subset',
    identity,
    browserChannel: profile?.config.browser.channel ?? options.browserChannel ?? loadServiceConfig().browser.channel,
    browsers: executables,
    sameBrowserBinary,
    debuggingEndpoints,
    harnessLines: Object.fromEntries(Object.entries(HARNESS_FILES).map(([arm, files]) => [arm,
      Object.fromEntries(files.map((file) => [file, codeLines(file)]))])),
    perturbationTiming: { thinkTimeMs: suite.thinkTimeMs, humanHoldMs: suite.thinkTimeMs * HUMAN_HOLD_FACTOR, agentRestartDelayMs: AGENT_RESTART_DELAY_MS },
    suite: options.suite,
    summaries: Object.fromEntries(scenarios.map((scenario) => [scenario.id, scenarioSummary(rows, scenario, definition.duplicateField)])),
    requirements,
    productAdvantage,
    rows,
    evidence,
  };
  writeFileSync(join(outDir, 'differentiation.json'), `${JSON.stringify(result, null, 2)}\n`);
  for (const requirement of requirements) {
    console.log(`${requirement.area}: ${requirement.status} ${JSON.stringify(requirement.improvement ?? {})}`);
  }
  console.log(`regressions: ${JSON.stringify(suiteRegressions)}; scripted: ${JSON.stringify(scriptedRegressions)}`);
  console.log(`product advantage established: ${productAdvantage.established}; same browser binary: ${result.sameBrowserBinary}; ${join(outDir, 'differentiation.json')}`);
  process.exit(0);
}

await main();
