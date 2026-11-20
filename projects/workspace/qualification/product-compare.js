#!/usr/bin/env node
// Matched live-planner investigation: Fawn vs stock Chromium + a durable issue/evidence tracker.
// The control gets the same planner, tools, source bytes, repository access and tracker contracts.
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, mkdtempSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { execFileSync } from 'node:child_process';
import { chromium } from 'playwright-core';
import { WorkspaceService } from '../src/service.js';
import { loadServiceConfig } from '../src/config.js';
import { createPlaywrightAdapter } from '../src/adapters/playwright-adapter.js';
import { queryPage, snapshotArgs, buildSnapshot } from '../src/adapters/page-query.js';
import { WorkspaceController } from '../src/client/controller.js';
import { InvestigationStore } from '../src/client/investigation.js';
import { startAgent, investigationContext } from '../src/client/agent.js';
import { createCliPlanner } from '../src/client/cli-planner.js';
import { repositoryEvidence, repositoryFiles } from '../src/client/repository.js';
import { sha256Hex } from '../src/journal.js';

const root = resolve(fileURLToPath(new URL('../../../', import.meta.url)));
const policy = JSON.parse(readFileSync(join(root, 'projects/workspace/config/fawn-investigation-comparison.json')));
const client = JSON.parse(readFileSync(join(root, 'projects/workspace/config/fawn-workspace-client.json')));
const help = 'Usage: node projects/workspace/qualification/product-compare.js --out DIR [--controlled]';
if (process.argv.includes('--help')) { console.log(help); process.exit(0); }
const args = process.argv.slice(2), controlled = args.includes('--controlled'), outIndex = args.indexOf('--out');
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--controlled') continue;
  if (args[i] === '--out' && args[i + 1] && !args[i + 1].startsWith('--')) { i++; continue; }
  throw Error(help);
}
const out = outIndex < 0 ? mkdtempSync(join(tmpdir(), 'fawn-investigation-comparison-')) : resolve(args[outIndex + 1]);
mkdirSync(out, { recursive: true });
const repository = join(out, 'repository'); mkdirSync(repository, { recursive: true });
const code = 'export async function checkout(send, order) { try { return await send(order); } catch { return send(order); } }\n';
writeFileSync(join(repository, 'checkout.js'), code);
const fixture = createServer((req, res) => {
  res.setHeader('content-type', 'text/html');
  res.end(`<title>API evidence</title><main>${req.url === '/details' ? 'A response timeout does not cancel an accepted charge. Query the receipt before resubmitting.' : 'Charge API: a request may complete before its response arrives. Without an idempotency key, each accepted POST creates a new charge.'}</main>`);
});
await new Promise(resolve => fixture.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${fixture.address().port}`;
let totalCost = 0;
const rawCalls = [];
function planner(arm) {
  if (controlled) return { identity: { model: 'controlled-preflight' }, next: async context => {
    const count = context.history.filter(event => event.event === 'tool-requested').length;
    const choices = [ ['capture', { pageId: 'main' }], ['capture', { pageId: 'api-details' }], ['repository_read', { path: 'checkout.js' }],
      ['record', { kind: 'finding', text: 'Blind retry after timeout can create a duplicate charge.', dependsOn: Object.keys(context.artifacts) }],
      ['record', { kind: 'question', text: 'Does the caller reuse a server-supported idempotency key?' }], ['finish', { summary: 'Evidence connected.' }] ];
    const [tool, input] = choices[count]; return { tool, input, usage: null };
  } };
  const provider = createCliPlanner({ executable: process.env.FAWN_CLAUDE_BIN ?? 'claude', model: policy.model,
    directory: join(out, arm, 'planner'), config: { ...client, cliMaxBudgetUsd: policy.maxTurnCostUsd } });
  return { identity: provider.identity, next: async (...input) => {
    if (totalCost + policy.maxTurnCostUsd > policy.maxTotalCostUsd) throw Error('Paired comparison spend ceiling reached');
    const started = performance.now();
    totalCost += policy.maxTurnCostUsd; // Reserve worst-case exposure before a call, including failed calls.
    let result;
    try { result = await provider.next(...input); }
    catch (error) {
      const measured = error.usage?.costUsd;
      if (Number.isFinite(measured) && measured >= 0) totalCost += measured - policy.maxTurnCostUsd;
      rawCalls.push({ arm, inputBytes: Buffer.byteLength(JSON.stringify(input[0])), durationMs: performance.now() - started,
        error: error.message, usage: error.usage ?? null, reservedCostUsd: Number.isFinite(measured) ? null : policy.maxTurnCostUsd });
      throw error;
    }
    if (result.usage?.models?.length !== 1 || result.usage.models[0] !== policy.model) throw Error('Planner reported a different model; matched comparison is not established');
    if (!Number.isFinite(result.usage?.costUsd) || result.usage.costUsd < 0) throw Error('Provider cost receipt missing; no further calls admitted');
    totalCost += result.usage.costUsd - policy.maxTurnCostUsd; rawCalls.push({ arm, inputBytes: Buffer.byteLength(JSON.stringify(input[0])), durationMs: performance.now() - started, usage: result.usage });
    return result;
  } };
}
function acceptance(project) {
  const artifacts = Object.values(project.artifacts), sources = artifacts.filter(value => value.kind === 'evidence');
  const sourceIds = new Set(sources.map(value => value.id));
  return { sourceCount: sources.length, questionCount: artifacts.filter(value => value.kind === 'question').length,
    sourcesBound: sources.every(value => value.source.sha256 === sha256Hex(value.source.content)),
    findingConnected: artifacts.some(value => value.kind === 'finding' && value.dependsOn.length === policy.requiredSources && value.dependsOn.every(id => sourceIds.has(id))),
    finished: project.run.status === 'completed', qualitativeReview: 'not-performed' };
}
const rows = [];
try {
  // Independent semantic repro: the first send commits then loses its response; the retry commits again.
  const { checkout } = await import(`data:text/javascript,${encodeURIComponent(code)}`);
  let charges = 0;
  await checkout(async () => { charges++; if (charges === 1) throw Error('response lost'); return 'receipt'; }, {});
  for (const arm of ['fawn', 'stock-browser-and-tracker']) {
    const started = performance.now(), armDir = join(out, arm); mkdirSync(armDir, { recursive: true });
    let controller, service, browser, store;
    try {
      const planned = planner(arm), config = { ...client, maxTurns: policy.maxTurnsPerArm };
      let projectId;
      if (arm === 'fawn') {
        service = await WorkspaceService.open({ stateDir: join(armDir, 'service'), config: loadServiceConfig(undefined, { browserChannel: 'chrome', headless: true }), createAdapter: createPlaywrightAdapter });
        controller = new WorkspaceController({ service, stateDir: armDir, config, planner: planned });
        ({ id: projectId } = await controller.create({ goal: policy.task, repositoryRoot: repository }));
        await controller.navigate(projectId, { pageId: 'main', url: origin });
        // Give both arms the same explicit page identifiers and initially opened source pages.
        await service.openPage({ ...controller.admin(projectId), pageId: 'api-details' });
        const metadata = await service.inspect(controller.admin(projectId));
        const second = metadata.pages.find(page => page.pageId !== 'main').pageId;
        await controller.navigate(projectId, { pageId: second, url: origin + '/details' });
        // The controller's page IDs are immutable; task text names the actual secondary identity.
        const task = policy.task.replaceAll('api-details', second);
        const preparationMs = performance.now() - started;
        await controller.delegate(projectId, { pageIds: ['main', second], origins: [origin], actionKinds: ['navigate'], task });
        await controller.active.get(projectId).done;
        store = controller.store;
        rows.push({ arm, preparationMs, completeTaskMs: performance.now() - started, acceptance: acceptance(store.get(projectId)), project: store.get(projectId) });
      } else {
        browser = await chromium.launchPersistentContext(join(armDir, 'profile'), { channel: 'chrome', headless: true });
        const main = browser.pages()[0] ?? await browser.newPage(), details = await browser.newPage();
        await main.goto(origin); await details.goto(origin + '/details');
        const pages = new Map([['main', main], ['api-details', details]]);
        store = new InvestigationStore(join(armDir, 'tracker')); projectId = 'stock-investigation';
        store.create({ id: projectId, goal: policy.task, repositoryRoot: repository });
        const startSequence = store.journal.records.at(-1).seq;
        const execute = async (tool, input) => {
          const pageId = input.pageId ?? 'main', page = pages.get(pageId);
          if (['capture', 'observe'].includes(tool)) {
            if (!page || new URL(page.url()).origin !== origin) throw Error('Control page exceeds task grant');
            const observation = buildSnapshot(await page.evaluate(queryPage, snapshotArgs(loadServiceConfig())), pages.size);
            if (tool === 'observe') return { ...observation, pageId };
            const content = observation.text;
            return store.revise(projectId, { kind: 'evidence', text: `Page evidence: ${observation.title}`, source: {
              kind: 'page', pageId, url: observation.url, content, sha256: sha256Hex(content) } });
          }
          if (tool === 'repository_files') return repositoryFiles(repository, client.maxRepositoryFiles);
          if (tool === 'repository_read') return store.revise(projectId, { kind: 'evidence', text: `Repository evidence: ${input.path}`,
            source: await repositoryEvidence(repository, input.path, client.maxEvidenceBytes) });
          if (tool === 'record' && input.kind !== 'evidence') return store.revise(projectId, input);
          throw Error('Read-only comparison admits no browser mutations');
        };
        const preparationMs = performance.now() - started;
        const run = startAgent({ projectId, store, planner: planned, execute, config, signal: new AbortController().signal,
          assertCurrent() {}, context: () => investigationContext(store.get(projectId), { task: policy.task,
            permissions: { pageIds: ['main', 'api-details'], origins: [origin], regions: null, actionKinds: ['navigate'] },
            startSequence, initialArtifacts: new Set(), shareRecords: false }) });
        await run.done;
        rows.push({ arm, preparationMs, completeTaskMs: performance.now() - started, acceptance: acceptance(store.get(projectId)), project: store.get(projectId) });
      }
    } finally { if (controller) await controller.close(); else store?.close(); if (service) await service.close(); if (browser) await browser.close(); }
  }
  const report = { schemaVersion: 1, classification: controlled ? 'controlled-planner preflight' : 'live-planner diagnostic paired probe',
    sourceCommit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
    sourceDirty: !!execFileSync('git', ['status', '--porcelain'], { cwd: root, encoding: 'utf8' }).trim(),
    policySha256: sha256Hex(JSON.stringify(policy)), armOrder: ['fawn', 'stock-browser-and-tracker'],
    cacheState: 'Provider-controlled cache; not reset between arms. One pair is diagnostic.', sourceRepro: { charges, expected: 2 }, rows, rawCalls, accountedCostUpperBoundUsd: totalCost,
    productAdvantageEstablished: false, limitations: [policy.promotion, 'Node host, browser and model costs are not interchangeable. CPU/GPU memory and p50/p95 require additional repetitions and instrumentation.',
      'This read-only investigation probe does not qualify interruption, multi-user experience or external retention. The independent workflow comparison retains those separate gates.'] };
  writeFileSync(join(out, 'product-comparison.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ report: join(out, 'product-comparison.json'), classification: report.classification, accountedCostUpperBoundUsd: totalCost,
    rows: rows.map(({ arm, completeTaskMs, acceptance }) => ({ arm, completeTaskMs, acceptance })), productAdvantageEstablished: false }));
} finally { await new Promise(resolve => fixture.close(resolve)); }
