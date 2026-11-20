#!/usr/bin/env node
// Freeze before learning, alternate paired arms, preserve failures and independently
// inspect real browser images. This command cannot reach a real shopping service.
import { mkdirSync, readFileSync, writeFileSync, existsSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { homedir } from 'node:os';
import { chromium } from 'playwright-core';
import { WorkspaceService } from '../../src/service.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { loadClientServiceConfig } from '../../src/client/browser-selection.js';
import { loadServiceConfig } from '../../src/config.js';
import { playwrightLaunchOptions } from '../../src/browser-launch.js';
import { ShoppingSession, createShoppingDriver } from '../../src/client/shopping-session.js';
import { PrivateJsonFile } from '../../src/client/private-json-file.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { sha256Hex } from '../../src/journal.js';
import { treeDigest, resultIdentity, inspectBrowserProcesses, waitForProfileRelease } from '../identity.js';
import { shoppingFixture, fixtureSite } from './fixture.js';
import { requestFor, trialCases } from './cases.js';
import { scriptDriver, controlledFieldPlanner } from './script-driver.js';
import { shoppingDecision } from './decision.js';

const args = process.argv.slice(2);
const option = name => { const i = args.indexOf(name); return i < 0 ? null : args[i + 1]; };
for (let i = 0; i < args.length; i++) {
  if (['--smoke', '--help'].includes(args[i])) continue;
  if (['--out', '--browser-config'].includes(args[i]) && args[i + 1] && !args[i + 1].startsWith('--')) { i++; continue; }
  throw Error('Unknown or incomplete option');
}
if (args.includes('--help')) { console.log('run.js --out NEW_DIR [--browser-config FAWN_PROFILE] [--smoke]'); process.exit(0); }
if (!option('--out')) throw Error('--out NEW_DIR is required');
const out = resolve(option('--out')), smoke = args.includes('--smoke');
if (existsSync(out)) throw Error('Output exists; preserve every prior attempt');
const contractBytes = readFileSync(new URL('./contract.json', import.meta.url));
const contract = JSON.parse(contractBytes);
const config = loadClientServiceConfig({ directory: join(homedir(), '.local/state/fawn-workspace'),
  browserChannel: 'fawn', browserConfig: option('--browser-config'), headless: true });
const scriptConfig = loadServiceConfig(undefined, { browserChannel: 'chrome', headless: true });
mkdirSync(out, { recursive: true, mode: 0o700 });
const currentSources = () => ({ runtime: treeDigest('projects/workspace/src'), harness: treeDigest('projects/workspace/qualification/shopping') });
const freeze = { schemaVersion: 1, frozenAt: new Date().toISOString(), contract, contractSha256: sha256Hex(contractBytes),
  source: currentSources(), identity: resultIdentity(), browser: config.browser, stockBrowser: scriptConfig.browser,
  smoke, arms: ['fawn-dag', 'stock-script'], cases: trialCases(contract, smoke), learningIndices: [100, 101],
  limits: ['Controlled storefront; no Best Buy qualification', 'Authored field-rule learning, no language-model speed claim',
    'No Cerebras agent is available', 'No account, card or real purchase is used', 'Script authoring labor is not measured'] };
writeFileSync(join(out, 'frozen.json'), JSON.stringify(freeze, null, 2), { flag: 'wx', mode: 0o600 });
const fixture = await shoppingFixture(), site = fixtureSite(fixture.origin), learned = new Map(), rows = [];
const file = path => new PrivateJsonFile(path, { maxBytes: 500000, lockWaitMs: 1000, lockRetryMs: 10 });
let serial = 0;

async function run(trial, arm, learning = false) {
  const operationId = `${arm}-${serial++}`, directory = join(out, operationId);
  mkdirSync(directory, { mode: 0o700 });
  const startUrl = fixture.add(operationId, trial.index, trial.fault), request = requestFor(trial.index);
  const attempts = file(join(directory, 'purchase.private.json')), progress = file(join(directory, 'script-progress.private.json'));
  const started = performance.now();
  let service, context, driver, admin, adapter, owner, purchaseAllowed = false, result, error = null, inspection = null;
  let preparationMs = null, taskStarted = null, restarted = false, priorTrace = [];
  const cache = learning ? learned : new Map([...learned].map(([key, value]) => [key, TraceDag.restore(value.export(), contract.limits)]));
  const open = async restart => {
    if (arm === 'fawn-dag') {
      service = await WorkspaceService.open({ stateDir: join(directory, 'service'), config,
        createAdapter: options => {
          adapter = createPlaywrightAdapter(options);
          const execute = adapter.execute.bind(adapter);
          adapter.execute = async (...values) => {
            const effect = await execute(...values);
            if (values[1].effect?.external && ['lost-acknowledgment', 'browser-restart', 'missing-receipt'].includes(trial.fault)) throw Error('Injected lost acknowledgment after merchant commit');
            return effect;
          };
          return adapter;
        } });
      if (!restart) admin = { workspaceId: operationId, ...await service.createWorkspace({ workspaceId: operationId }) };
      await service.grantAuthorization({ ...admin, grantId: `browse-${restart}`, ownerId: 'agent', intents: ['shopping'],
        actionKinds: ['navigate', 'click', 'fill', 'select'], targetOrigins: [fixture.origin] });
      await service.grantAuthorization({ ...admin, grantId: `browse-forms-${restart}`, ownerId: 'agent', intents: ['shopping-browse'],
        actionKinds: ['submit'], targetOrigins: [fixture.origin] });
      owner = { workspaceId: operationId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };
      driver = createShoppingDriver({ service, owner });
    } else {
      context = await chromium.launchPersistentContext(join(directory, 'profile'), {
        ...playwrightLaunchOptions(scriptConfig.browser), headless: true, chromiumSandbox: true });
      const page = context.pages()[0] ?? await context.newPage(); page.setDefaultTimeout(config.dispatch.actionTimeoutMs);
      driver = scriptDriver({ page, config, progress, operationId, fault: trial.fault, purchaseAllowed: () => purchaseAllowed });
    }
    await driver.observe(); // Both arms prepare an actual blank browser before prompt timing.
  };
  const navigate = async url => {
    const observation = await driver.observe();
    const outcome = await driver.act(observation, { kind: 'navigate', target: { url } });
    if (outcome.outcome !== 'completed') throw Error('Navigation failed');
  };
  const session = () => new ShoppingSession({ driver, site, request, cache, planner: controlledFieldPlanner,
    mode: arm === 'stock-script' ? 'script' : learning ? 'learn' : 'reuse', limits: contract.limits, attempts, operationId,
    approvePurchase: async ({ quoteHash }) => {
      if (service) {
        await service.grantAuthorization({ ...admin, grantId: 'purchase', ownerId: 'agent', intents: ['shopping'],
          actionKinds: ['submit'], targetOrigins: [fixture.origin] });
        if (trial.fault === 'revoked-purchase') await service.revokeAuthorization({ ...admin, grantId: 'purchase' });
      }
      purchaseAllowed = trial.fault !== 'revoked-purchase';
      return { quoteHash }; // Fixture-only authorization; unavailable for real merchant origins.
    } });
  try {
    await open(false);
    preparationMs = performance.now() - started;
    taskStarted = performance.now();
    await navigate(startUrl);
    result = await session().run();
    if (result.status === 'unknown') {
      const stats = result.stats;
      if (trial.fault === 'browser-restart') {
        priorTrace = driver.trace;
        await service?.close(); service = null; await context?.close(); context = null;
        await open(true); restarted = true;
        await navigate(`${fixture.origin}/${operationId}/receipt`);
      }
      result = { ...await session().recover(), stats };
    }
  } catch (caught) { error = caught.message; }
  const completeMs = performance.now() - started, taskMs = taskStarted === null ? null : performance.now() - taskStarted;
  const oracle = fixture.oracle(operationId);
  const completed = result?.completed === true && oracle.completed;
  let passed = !error && oracle.wrongOrders === 0 && oracle.duplicateOrders === 0
    && (trial.expected === 'completed' ? completed : result?.completed === false);
  if (trial.expected === 'stopped' && trial.fault !== 'missing-receipt') passed &&= oracle.submissions === 0;
  if (trial.fault === 'missing-receipt') passed &&= result?.status === 'unknown' && oracle.submissions === 1;
  if (trial.fault === 'browser-restart') passed &&= restarted;
  try {
    inspection = inspectBrowserProcesses(process.pid, directory);
    if (arm === 'fawn-dag') passed &&= inspection.executables.length > 0
      && inspection.executables.every(value => value.sha256 === config.browser.fawnBuild.executable.sha256);
  } catch (caught) { error = caught.message; passed = false; }
  finally {
    await service?.close(); await context?.close(); await waitForProfileRelease(directory);
    rmSync(join(directory, 'profile'), { recursive: true, force: true });
    rmSync(join(directory, 'service/profiles'), { recursive: true, force: true });
  }
  const row = { caseId: trial.id, index: trial.index, fault: trial.fault, arm, learning, preparationMs, taskMs, completeMs,
    completed, passed, result, error, oracle, inspection, trace: [...priorTrace, ...(driver?.trace ?? [])],
    cleanup: { profilesReleased: true, browserProfilesRemoved: true }, restarted };
  rows.push(row);
  writeFileSync(join(directory, 'result.json'), JSON.stringify(row, null, 2), { mode: 0o600 });
  writeFileSync(join(out, 'rows.json'), JSON.stringify(rows, null, 2), { mode: 0o600 });
  console.log(JSON.stringify({ case: trial.id, arm, passed, completed, completeMs: Math.round(completeMs), reason: error ?? result?.reason ?? result?.status }));
  return row;
}

try {
  for (const index of freeze.learningIndices) {
    const result = await run({ id: `learn-${index}`, index, fault: null, expected: 'completed' }, 'fawn-dag', true);
    if (!result.passed) throw Error('Learning failed; evaluation not started');
  }
  writeFileSync(join(out, 'cache.private.json'), JSON.stringify([...learned].map(([key, dag]) => [key, dag.export()])), { mode: 0o600 });
  for (let i = 0; i < freeze.cases.length; i++) {
    for (const arm of i % 2 ? ['stock-script', 'fawn-dag'] : ['fawn-dag', 'stock-script']) await run(freeze.cases[i], arm);
  }
} catch (error) { writeFileSync(join(out, 'failure.json'), JSON.stringify({ error: error.message })); process.exitCode = 1; }
finally {
  await fixture.close();
  const sourceUnchanged = JSON.stringify(currentSources()) === JSON.stringify(freeze.source);
  const decision = shoppingDecision(rows, freeze.cases, contract, { sourceUnchanged, smoke });
  writeFileSync(join(out, 'report.json'), JSON.stringify({ ...decision, frozenSha256: sha256Hex(readFileSync(join(out, 'frozen.json'))) }, null, 2));
  if (!decision.correctness || !sourceUnchanged) process.exitCode = 1;
  console.log(JSON.stringify(decision));
}
