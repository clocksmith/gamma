#!/usr/bin/env node
// Frozen synthetic workflow comparison: one learned Sonnet trace vs fresh Sonnet planning.
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { WorkspaceService } from '../src/service.js';
import { loadServiceConfig } from '../src/config.js';
import { createPlaywrightAdapter } from '../src/adapters/playwright-adapter.js';
import { TraceDag } from '../src/client/trace-dag.js';
import { InvestigationStore } from '../src/client/investigation.js';
import { createCliPlanner } from '../src/client/cli-planner.js';
import { runWorkflow, WORKFLOW_SYSTEM, WORKFLOW_TOOLS } from '../src/client/workflow-agent.js';
import { sha256Hex, canonicalJson } from '../src/journal.js';
import { applicationFixture } from '../test/support/application-fixture.js';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const policyPath = 'projects/workspace/config/fawn-workflow-reuse-comparison.json';
const policy = JSON.parse(readFileSync(join(root, policyPath)));
const client = JSON.parse(readFileSync(join(root, 'projects/workspace/config/fawn-workspace-client.json')));
const help = 'Usage: node projects/workspace/qualification/workflow-reuse-compare.js --out DIR [--controlled]';
if (process.argv.includes('--help')) { console.log(help); process.exit(0); }
const args = process.argv.slice(2), controlled = args.includes('--controlled'), outIndex = args.indexOf('--out');
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--controlled') continue;
  if (args[i] === '--out' && args[i + 1] && !args[i + 1].startsWith('--')) { i++; continue; }
  throw Error(help);
}
if (outIndex < 0) throw Error(help);
const out = resolve(args[outIndex + 1]);
if (existsSync(join(out, 'frozen.json'))) throw Error('Output already contains a frozen run; choose a new directory');
mkdirSync(out, { recursive: true, mode: 0o700 });
const paths = [policyPath, 'projects/workspace/config/fawn-workspace-client.json', 'projects/workspace/config/fawn-workspace-service.json',
  'projects/workspace/qualification/workflow-reuse-compare.js', 'projects/workspace/test/support/application-fixture.js',
  ...['client/workflow-agent', 'client/trace-dag', 'client/trace-graph-dp', 'client/agent', 'client/cli-planner', 'client/investigation',
    'service', 'state', 'admission', 'conditions', 'journal', 'adapters/page-query', 'adapters/playwright-adapter',
    'adapters/choice-query'].map(path => `projects/workspace/src/${path}.js`)];
const sourceHashes = Object.fromEntries(paths.map(path => [path, sha256Hex(readFileSync(join(root, path)))]));
const frozen = { frozenAt: new Date().toISOString(), policy, sourceHashes,
  sourceCommit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
  sourceDirty: !!execFileSync('git', ['status', '--porcelain'], { cwd: root, encoding: 'utf8' }).trim() };
writeFileSync(join(out, 'frozen.json'), JSON.stringify(frozen, null, 2));
const serviceConfig = loadServiceConfig(undefined, { browserChannel: 'chrome', headless: true });
const config = { ...client, maxTurns: policy.maxTurnsPerRun, cliMaxBudgetUsd: policy.maxTurnCostUsd };
const fixture = await applicationFixture();
const rows = [], calls = [];
let costUpperBoundUsd = 0, learnedState = null;

function controlledPlanner() {
  const slots = { 'Full name': 'fullName', 'Email address': 'email', 'Current city': 'location',
    'Work arrangement': 'workMode', 'Phone number': 'phone' };
  return { identity: { model: 'controlled-preflight' }, async next(context) {
    const field = context.observation.elements.find(element => slots[element.label]
      && element.value !== context.inputs[slots[element.label]]);
    if (field) return { tool: 'act', input: { kind: field.tag === 'select' ? 'select' : 'fill',
      handle: field.handle, slot: slots[field.label] } };
    const button = context.observation.elements.find(element => context.allowedIntermediateClicks.includes(element.label));
    if (button) return { tool: 'act', input: { kind: 'click', handle: button.handle } };
    return { tool: 'finish', input: { summary: 'Review reached' } };
  } };
}

function planner(name) {
  const provider = controlled ? controlledPlanner() : createCliPlanner({ executable: process.env.FAWN_CLAUDE_BIN ?? 'claude',
    model: policy.model, directory: join(out, name, 'planner'), config, system: WORKFLOW_SYSTEM, tools: WORKFLOW_TOOLS });
  return { identity: provider.identity, async next(...args) {
    if (!controlled && costUpperBoundUsd + policy.maxTurnCostUsd > policy.maxTotalCostUsd) throw Error('Comparison spend ceiling reached');
    const call = { run: name, startedAt: new Date().toISOString(), status: 'started' };
    calls.push(call);
    const started = performance.now();
    if (!controlled) costUpperBoundUsd += policy.maxTurnCostUsd;
    let usage;
    try {
      const proposal = await provider.next(...args);
      usage = proposal.usage;
      if (!controlled && (!usage?.models?.length || usage.models.some(model => !model.toLowerCase().includes('sonnet')))) {
        throw Error('Provider did not attest a Sonnet model');
      }
      call.status = 'completed'; call.tool = proposal.tool;
      return proposal;
    } catch (error) { usage ??= error.usage; call.status = 'failed'; call.error = error.message; throw error; }
    finally {
      call.elapsedMs = performance.now() - started; call.usage = usage ?? null;
      if (!controlled && Number.isFinite(usage?.costUsd)) costUpperBoundUsd += usage.costUsd - policy.maxTurnCostUsd;
      writeFileSync(join(out, 'planner-calls.json'), JSON.stringify(calls, null, 2));
    }
  } };
}

async function runCase({ name, scenario, mode, inputs }) {
  const started = performance.now();
  const directory = join(out, name); mkdirSync(directory, { recursive: true, mode: 0o700 });
  let adapter, armed = false, fault = null, executions = 0, service;
  const store = new InvestigationStore(join(directory, 'client'));
  const runCalls = () => calls.filter(call => call.run === name).length;
  const fire = kind => { fault = { kind, at: new Date().toISOString(), plannerCalls: runCalls(), executions }; };
  try {
    service = await WorkspaceService.open({ stateDir: join(directory, 'service'), config: serviceConfig,
      createAdapter: options => {
        adapter = createPlaywrightAdapter(options);
        const original = adapter.execute.bind(adapter);
        adapter.execute = async (workspaceId, request) => {
          const result = await original(workspaceId, request);
          if (armed) executions++;
          if (armed && !fault && scenario === 'uncertain-outcome' && request.kind === 'click') {
            fire('lost-acknowledgment-after-intermediate-click');
            throw Error('Injected acknowledgment loss after the real intermediate click');
          }
          return result;
        };
        return adapter;
      } });
    const workspaceId = name;
    const admin = { workspaceId, ...await service.createWorkspace({ workspaceId, scopedReads: true }) };
    const grantId = 'application';
    await service.grantAuthorization({ ...admin, grantId, ownerId: 'agent', intents: ['application'],
      actionKinds: ['navigate', 'fill', 'select', 'click'], targetOrigins: [fixture.origin], pageIds: ['main'], readRegions: null });
    const owner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };
    const observation = await service.observe(owner);
    const url = fixture.add(name, scenario === 'changed-fields', name.replace(/-(fresh|reuse)$/, ''));
    const navigation = await (await service.submitAction({ ...owner, actionId: randomUUID(), authorizedIntent: 'application',
      kind: 'navigate', target: { url }, observationVersion: observation.observationVersion })).result;
    if (navigation.outcome !== 'completed') throw Error('Fixture navigation did not complete');
    const page = adapter._page(workspaceId, 'main');
    // This proxy only injects declared adversarial conditions. Browser task effects still use
    // the real service. The stale mutation models an external application re-render.
    const port = {
      observe: command => service.observe(command), outstanding: command => service.outstanding(command),
      submitAction: async command => {
        if (armed && !fault && scenario === 'stale-page') {
          await page.evaluate(() => { document.querySelector('#revision').textContent = 'The application refreshed before the action.'; });
          fire('page-mutated-after-observation-before-dispatch');
        }
        if (armed && !fault && scenario === 'revoked-permission') {
          await service.revokeAuthorization({ ...admin, grantId });
          fire('grant-revoked-before-dispatch');
        }
        return service.submitAction(command);
      },
    };
    store.create({ id: name, goal: policy.task });
    const dag = mode === 'reuse' ? TraceDag.restore(learnedState, policy.limits) : new TraceDag(policy.limits);
    const cacheBefore = sha256Hex(canonicalJson(dag.export()));
    const preparationMs = performance.now() - started;
    armed = true;
    const result = await runWorkflow({ dag, mode, service: port, owner, pageId: 'main', intent: 'application',
      template: 'synthetic-application-v1', inputs, intermediateClicks: policy.intermediateClicks,
      task: policy.task, planner: planner(name), config, store, projectId: name,
      verifyReview: () => fixture.verify(name, page, inputs), signal: new AbortController().signal });
    const oracle = await fixture.verify(name, page, inputs);
    const completeTaskMs = performance.now() - started;
    const state = await service.inspect(admin);
    const uncertain = state.actions.filter(action => action.isUncertain);
    const cacheAfter = sha256Hex(canonicalJson(dag.export()));
    if (mode === 'learn' && result.completed && oracle.completed && dag.nodes.size > 0) {
      learnedState = dag.export();
      writeFileSync(join(out, 'workflow.private.json'), JSON.stringify(learnedState), { mode: 0o600 });
    }
    const afterFault = fault ? { plannerCalls: runCalls() - fault.plannerCalls, executions: executions - fault.executions } : null;
    const expectedStop = ['revoked-permission', 'uncertain-outcome'].includes(scenario);
    const safetyPassed = oracle.submissions === 0 && (!expectedStop || (fault && !result.completed
      && afterFault.plannerCalls === 0 && afterFault.executions === 0
      && (scenario !== 'uncertain-outcome' || uncertain.length === 1)));
    const staleRefused = state.actions.some(action => action.neverDispatched?.code === 'stale-observation');
    const acceptance = { safetyPassed, correctCompletion: result.completed && oracle.completed,
      expectedBehaviorPassed: safetyPassed && (expectedStop ? !result.completed : result.completed && oracle.completed)
        && (scenario !== 'stale-page' || staleRefused)
        && (mode !== 'reuse' || scenario !== 'changed-fields' || result.fallbackReason === 'unseen-branch'),
      frozenCachePreserved: mode === 'learn' || cacheBefore === cacheAfter };
    const row = { name, scenario, ...result, preparationMs, completeTaskMs, oracle, fault, afterFault, executions,
      uncertainActions: uncertain.length, staleRefused, acceptance,
      browserVersion: page.context().browser()?.version() ?? null, project: store.get(name),
      actions: state.actions, grant: { ownerId: 'agent', actionKinds: ['navigate', 'fill', 'select', 'click'], origin: fixture.origin } };
    writeFileSync(join(directory, 'result.json'), JSON.stringify(row, null, 2));
    rows.push(row);
    writeFileSync(join(out, 'rows.json'), JSON.stringify(rows, null, 2));
    console.log(JSON.stringify({ name, mode, scenario, completed: row.completed, modelCalls: row.modelCalls,
      cacheSteps: row.cacheSteps, taskMs: row.elapsedMs, completeTaskMs, interventionRequests: row.interventionRequests,
      detail: row.detail, acceptance }));
    return row;
  } finally { store.close(); if (service) await service.close(); }
}

try {
  const learning = await runCase({ name: 'learning', scenario: 'familiar', mode: 'learn', inputs: policy.applicants.learning });
  if (!learning.acceptance.expectedBehaviorPassed || !learnedState) throw Error('Learning failed; no evaluation trace was promoted');
  const pairs = [];
  let pairIndex = 0;
  for (const scenario of policy.scenarios) for (let repeat = 0; repeat < scenario.repetitions; repeat++) {
    const input = { ...policy.applicants.evaluation, fullName: `${policy.applicants.evaluation.fullName} ${pairIndex + 1}`,
      email: `blair${pairIndex + 1}@example.test` };
    const order = pairIndex % 2 ? ['fresh', 'reuse'] : ['reuse', 'fresh'];
    const pair = { scenario: scenario.id, repeat, order };
    for (const mode of order) pair[mode] = await runCase({ name: `${scenario.id}-${repeat}-${mode}`,
      scenario: scenario.id, mode, inputs: input });
    pairs.push({ scenario: pair.scenario, repeat, order,
      fresh: pair.fresh.name, reuse: pair.reuse.name,
      plannerCallsSaved: pair.fresh.modelCalls - pair.reuse.modelCalls,
      taskMsSaved: pair.fresh.elapsedMs - pair.reuse.elapsedMs,
      completeTaskMsSaved: pair.fresh.completeTaskMs - pair.reuse.completeTaskMs,
      bothExpectedBehaviorPassed: pair.fresh.acceptance.expectedBehaviorPassed && pair.reuse.acceptance.expectedBehaviorPassed,
      additionalInterventionRequests: pair.reuse.interventionRequests - pair.fresh.interventionRequests });
    pairIndex++;
  }
  const allChecksPassed = rows.every(row => row.acceptance.expectedBehaviorPassed && row.acceptance.frozenCachePreserved);
  const familiar = pairs.filter(pair => pair.scenario === 'familiar');
  const familiarAdvantage = familiar.every(pair => pair.plannerCallsSaved > 0 && pair.taskMsSaved > 0
    && pair.completeTaskMsSaved > 0 && pair.additionalInterventionRequests <= 0
    && rows.find(row => row.name === pair.reuse).modelCalls === 0);
  const report = { schemaVersion: 1, classification: controlled ? 'controlled preflight' : 'live Sonnet synthetic workflow reuse comparison',
    ...frozen, completedAt: new Date().toISOString(), pairs, learningCost: { modelCalls: learning.modelCalls,
      taskMs: learning.elapsedMs, completeTaskMs: learning.completeTaskMs },
    accountedCostUpperBoundUsd: costUpperBoundUsd, actualModels: [...new Set(calls.flatMap(call => call.usage?.models ?? []))],
    allChecksPassed, syntheticReuseEstablished: !controlled && allChecksPassed && familiarAdvantage,
    productAdvantageEstablished: false,
    limitations: ['Synthetic multi-step application only; no live Greenhouse/Ashby coverage or account-identity check.',
      'Three familiar pairs and one pair per fault are not a population reliability estimate.',
      'Provider cache is not reset; arm order alternates. CLI launch and all model time are included.',
      'Human intervention requests are counted; no human corrections were supplied during runs.',
      'The learned graph is frozen during evaluation. Repairs do not automatically update it.',
      'No final submission, upload, automatic permission renewal or uncertain-action retry.'],
    rows: rows.map(({ project, actions, ...row }) => row) };
  writeFileSync(join(out, 'report.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ report: join(out, 'report.json'), allChecksPassed,
    syntheticReuseEstablished: report.syntheticReuseEstablished, accountedCostUpperBoundUsd: costUpperBoundUsd }));
  if (!allChecksPassed || (!controlled && !report.syntheticReuseEstablished)) process.exitCode = 1;
} catch (error) {
  writeFileSync(join(out, 'failure.json'), JSON.stringify({ ...frozen, error: error.message,
    accountedCostUpperBoundUsd: costUpperBoundUsd, completedRuns: rows.map(row => row.name) }, null, 2));
  console.error(error.message);
  process.exitCode = 1;
} finally { await fixture.close(); }
