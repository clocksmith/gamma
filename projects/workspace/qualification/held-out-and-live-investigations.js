#!/usr/bin/env node
// Held-out engineering investigations and real public HTTPS live-site workspace checks.
// Evaluates WorkspaceService, WorkspaceController, InvestigationStore and engineering
// investigation recovery on stock Chrome, strictly separate from Doe GPU claims.
import { createServer } from 'node:http';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
import { WorkspaceService } from '../src/service.js';
import { loadServiceConfig } from '../src/config.js';
import { createPlaywrightAdapter } from '../src/adapters/playwright-adapter.js';
import { buildSnapshot, queryPage, snapshotArgs } from '../src/adapters/page-query.js';
import { WorkspaceController } from '../src/client/controller.js';
import { InvestigationStore } from '../src/client/investigation.js';
import { investigationContext, startAgent } from '../src/client/agent.js';
import { repositoryEvidence, repositoryFiles } from '../src/client/repository.js';
import { createOwnerSession } from '../src/workflows/owner-session.js';
import {
  recoverEngineeringInvestigation,
  runEngineeringInvestigation,
} from '../src/workflows/engineering-investigation.js';
import { sha256Hex } from '../src/journal.js';

const ROOT = resolve(fileURLToPath(new URL('../../../', import.meta.url)));
const CLIENT_CONFIG = JSON.parse(readFileSync(join(ROOT, 'projects/workspace/config/fawn-workspace-client.json'), 'utf8'));
const USAGE = 'Usage: node projects/workspace/qualification/held-out-and-live-investigations.js [--out DIR] [--offline]';

function scriptPlanner(steps) {
  let cursor = 0;
  return {
    identity: { model: 'held-out-deterministic-driver' },
    next: async (context) => {
      const step = steps[cursor++];
      if (!step) return { tool: 'finish', input: { summary: 'Completed.' }, usage: null };
      const [tool, rawInput] = typeof step === 'function' ? step(context) : step;
      return { tool, input: rawInput, usage: null };
    },
  };
}

function summarizeArtifacts(project, requiredEvidence) {
  const artifacts = Object.values(project.artifacts);
  const evidence = artifacts.filter((item) => item.kind === 'evidence');
  const ids = new Set(evidence.map((item) => item.id));
  return {
    evidenceCount: evidence.length,
    sourcesBound: evidence.length >= requiredEvidence
      && evidence.every((item) => item.source?.sha256 === sha256Hex(item.source.content)),
    findingConnected: artifacts.some((item) => item.kind === 'finding'
      && item.dependsOn.length >= requiredEvidence
      && item.dependsOn.filter((id) => ids.has(id)).length >= requiredEvidence),
    questionCount: artifacts.filter((item) => item.kind === 'question').length,
    decisionCount: artifacts.filter((item) => item.kind === 'decision').length,
    finished: project.run?.status === 'completed',
  };
}

async function detectChromeIdentity(workDir) {
  const ctx = await chromium.launchPersistentContext(join(workDir, 'chrome-probe'), {
    channel: 'chrome',
    headless: true,
  });
  try {
    const version = ctx.browser()?.version() ?? 'unknown';
    const cdp = await ctx.browser().newBrowserCDPSession();
    const cmd = await cdp.send('Browser.getBrowserCommandLine');
    const exe = cmd.arguments?.[0] && existsSync(cmd.arguments[0]) ? realpathSync(cmd.arguments[0]) : null;
    return {
      channel: 'chrome',
      version,
      executablePath: exe,
      executableSha256: exe ? sha256Hex(readFileSync(exe)) : null,
    };
  } finally {
    await ctx.close();
  }
}

async function runPairedReadInvestigation({
  id,
  category,
  goal,
  pagesSpec,
  ungrantedUrl,
  repositorySpec,
  findingText,
  questionText,
  outDir,
}) {
  const scenarioDir = join(outDir, id);
  rmSync(scenarioDir, { recursive: true, force: true });
  mkdirSync(scenarioDir, { recursive: true });
  const repoDir = join(scenarioDir, 'repo');
  mkdirSync(repoDir, { recursive: true });
  if (repositorySpec) writeFileSync(join(repoDir, repositorySpec.path), repositorySpec.content);
  const allowedOrigins = [...new Set(pagesSpec.map((entry) => new URL(entry.url).origin))];
  const requiredEvidence = pagesSpec.length + (repositorySpec ? 1 : 0);
  const arms = {};

  for (const arm of ['fawn', 'stock-browser-and-tracker']) {
    const started = performance.now();
    const armDir = join(scenarioDir, arm);
    mkdirSync(armDir, { recursive: true });
    let service;
    let controller;
    let browser;
    let store;
    try {
      if (arm === 'fawn') {
        service = await WorkspaceService.open({
          stateDir: join(armDir, 'service'),
          config: loadServiceConfig(undefined, { browserChannel: 'chrome', headless: true }),
          createAdapter: createPlaywrightAdapter,
        });
        const actualPageIds = ['main'];
        const steps = [];
        controller = new WorkspaceController({
          service,
          stateDir: armDir,
          config: { ...CLIENT_CONFIG, maxTurns: 12 },
          planner: scriptPlanner(steps),
        });
        const { id: projectId } = await controller.create({
          goal,
          repositoryRoot: repositorySpec ? repoDir : null,
        });
        const navStart = performance.now();
        await controller.navigate(projectId, { pageId: 'main', url: pagesSpec[0].url });
        for (let idx = 1; idx < pagesSpec.length; idx++) {
          await service.openPage({ ...controller.admin(projectId), pageId: pagesSpec[idx].key });
          const inspected = await service.inspect(controller.admin(projectId));
          const createdId = inspected.pages.find((page) => !actualPageIds.includes(page.pageId)).pageId;
          actualPageIds.push(createdId);
          await controller.navigate(projectId, { pageId: createdId, url: pagesSpec[idx].url });
        }
        const navigationSetupMs = Number((performance.now() - navStart).toFixed(2));
        for (const pageId of actualPageIds) steps.push(['capture', { pageId }]);
        if (repositorySpec) steps.push(['repository_read', { path: repositorySpec.path }]);
        steps.push(
          (ctx) => ['record', { kind: 'finding', text: findingText, dependsOn: Object.keys(ctx.artifacts) }],
          ['record', { kind: 'question', text: questionText }],
          ['finish', { summary: 'Evidence bound and connected.' }],
        );
        const delegateStart = performance.now();
        await controller.delegate(projectId, {
          pageIds: actualPageIds,
          origins: allowedOrigins,
          actionKinds: ['navigate'],
          task: goal,
        });
        await controller.active.get(projectId).done;
        const delegatedMs = Number((performance.now() - delegateStart).toFixed(2));
        const completeTaskMs = Number((performance.now() - started).toFixed(2));
        let ungrantedRejected = null;
        let ungrantedProbeMs = null;
        if (ungrantedUrl) {
          const probeStart = performance.now();
          await service.openPage({ ...controller.admin(projectId), pageId: 'ungranted-probe' });
          const inspected = await service.inspect(controller.admin(projectId));
          const extraId = inspected.pages.find((page) => !actualPageIds.includes(page.pageId)).pageId;
          await controller.navigate(projectId, { pageId: extraId, url: ungrantedUrl });
          await service.grantAuthorization({
            ...controller.admin(projectId),
            grantId: 'narrow-origin-probe',
            ownerId: 'probe-reader',
            intents: ['delegated-task'],
            targetOrigins: allowedOrigins,
            actionKinds: ['navigate'],
            pageIds: [...actualPageIds, extraId],
            readRegions: null,
          });
          const probeOwner = await service.assignOwner({ ...controller.admin(projectId), ownerId: 'probe-reader' });
          try {
            await service.observe({
              workspaceId: projectId,
              ownerId: 'probe-reader',
              ownerGeneration: probeOwner.ownerGeneration,
              pageId: extraId,
            });
            ungrantedRejected = false;
          } catch {
            ungrantedRejected = true;
          }
          await service.revokeAuthorization({ ...controller.admin(projectId), grantId: 'narrow-origin-probe' });
          await controller.takeOver(projectId);
          ungrantedProbeMs = Number((performance.now() - probeStart).toFixed(2));
        }
        const project = controller.store.get(projectId);
        arms[arm] = {
          navigationSetupMs,
          delegatedMs,
          completeTaskMs,
          ungrantedProbeMs,
          ungrantedOriginRejected: ungrantedRejected,
          acceptance: summarizeArtifacts(project, requiredEvidence),
          capturedUrls: Object.values(project.artifacts)
            .filter((item) => item.kind === 'evidence' && item.source?.url)
            .map((item) => ({ url: item.source.url, sha256: item.source.sha256, bytes: item.source.content.length })),
        };
      } else {
        browser = await chromium.launchPersistentContext(join(armDir, 'profile'), {
          channel: 'chrome',
          headless: true,
        });
        const navStart = performance.now();
        const pageMap = new Map();
        for (let idx = 0; idx < pagesSpec.length; idx++) {
          const page = idx === 0 ? (browser.pages()[0] ?? await browser.newPage()) : await browser.newPage();
          await page.goto(pagesSpec[idx].url, { waitUntil: 'domcontentloaded' });
          pageMap.set(pagesSpec[idx].key, page);
        }
        const navigationSetupMs = Number((performance.now() - navStart).toFixed(2));
        store = new InvestigationStore(join(armDir, 'tracker'));
        const projectId = `${id}-control`;
        store.create({ id: projectId, goal, repositoryRoot: repositorySpec ? repoDir : null });
        const startSequence = store.journal.records.at(-1).seq;
        const steps = pagesSpec.map((entry) => ['capture', { pageId: entry.key }]);
        if (repositorySpec) steps.push(['repository_read', { path: repositorySpec.path }]);
        steps.push(
          (ctx) => ['record', { kind: 'finding', text: findingText, dependsOn: Object.keys(ctx.artifacts) }],
          ['record', { kind: 'question', text: questionText }],
          ['finish', { summary: 'Evidence bound and connected.' }],
        );
        const execute = async (tool, input) => {
          if (tool === 'capture' || tool === 'observe') {
            const page = pageMap.get(input.pageId);
            if (!page || !allowedOrigins.includes(new URL(page.url()).origin)) {
              throw Error('Control page outside allowed origin');
            }
            const obs = buildSnapshot(await page.evaluate(queryPage, snapshotArgs(loadServiceConfig())), pageMap.size);
            if (tool === 'observe') return { ...obs, pageId: input.pageId };
            return store.revise(projectId, {
              kind: 'evidence',
              text: `Page evidence: ${obs.title || obs.url}`,
              source: { kind: 'page', pageId: input.pageId, url: obs.url, content: obs.text, sha256: sha256Hex(obs.text) },
            });
          }
          if (tool === 'repository_files') return repositoryFiles(repoDir, CLIENT_CONFIG.maxRepositoryFiles);
          if (tool === 'repository_read') {
            return store.revise(projectId, {
              kind: 'evidence',
              text: `Repository evidence: ${input.path}`,
              source: await repositoryEvidence(repoDir, input.path, CLIENT_CONFIG.maxEvidenceBytes),
            });
          }
          if (tool === 'record' && input.kind !== 'evidence') return store.revise(projectId, input);
          throw Error(`Unsupported control tool ${tool}`);
        };
        const delegateStart = performance.now();
        const run = startAgent({
          projectId,
          store,
          planner: scriptPlanner(steps),
          execute,
          config: { ...CLIENT_CONFIG, maxTurns: 12 },
          signal: new AbortController().signal,
          assertCurrent() {},
          context: () => investigationContext(store.get(projectId), {
            task: goal,
            permissions: {
              pageIds: pagesSpec.map((entry) => entry.key),
              origins: allowedOrigins,
              regions: null,
              actionKinds: ['navigate'],
            },
            startSequence,
            initialArtifacts: new Set(),
            shareRecords: false,
          }),
        });
        await run.done;
        const project = store.get(projectId);
        arms[arm] = {
          navigationSetupMs,
          delegatedMs: Number((performance.now() - delegateStart).toFixed(2)),
          completeTaskMs: Number((performance.now() - started).toFixed(2)),
          acceptance: summarizeArtifacts(project, requiredEvidence),
        };
      }
    } finally {
      if (controller) await controller.close();
      else store?.close();
      if (service) await service.close();
      if (browser) await browser.close();
    }
  }

  const passed = arms.fawn.acceptance.finished
    && arms.fawn.acceptance.sourcesBound
    && arms.fawn.acceptance.findingConnected
    && (ungrantedUrl ? arms.fawn.ungrantedOriginRejected === true : true)
    && arms['stock-browser-and-tracker'].acceptance.finished
    && arms['stock-browser-and-tracker'].acceptance.sourcesBound
    && arms['stock-browser-and-tracker'].acceptance.findingConnected;
  return { id, category, passed, arms };
}

async function runHeldOutHumanTakeover(origin, outDir) {
  const armDir = join(outDir, 'webhook-replay-human-takeover');
  rmSync(armDir, { recursive: true, force: true });
  const repoDir = join(armDir, 'repo');
  mkdirSync(repoDir, { recursive: true });
  writeFileSync(
    join(repoDir, 'webhook-handler.js'),
    'export async function handleWebhook(db, payload) { return db.insertDelivery(payload.eventId, payload); }\n',
  );
  let service;
  let controller;
  let phase = 1;
  let staleAgentOwner = null;
  let staleGenerationRejected = false;
  try {
    service = await WorkspaceService.open({
      stateDir: join(armDir, 'service'),
      config: loadServiceConfig(undefined, { browserChannel: 'chrome', headless: true }),
      createAdapter: createPlaywrightAdapter,
    });
    const planner = {
      identity: { model: 'held-out-takeover-driver' },
      next: async (context) => {
        const turns = context.history.filter((entry) => entry.event === 'tool-requested').length;
        if (phase === 1) {
          if (turns === 0) return { tool: 'capture', input: { pageId: 'main' }, usage: null };
          staleAgentOwner = { ...controller.owners.get(context.projectId) };
          await controller.takeOverNow(context.projectId);
          return { tool: 'capture', input: { pageId: 'main' }, usage: null };
        }
        if (turns === 0) return { tool: 'repository_read', input: { path: 'webhook-handler.js' }, usage: null };
        if (turns === 1) {
          return {
            tool: 'record',
            input: {
              kind: 'finding',
              text: 'Webhook redeliveries insert duplicate rows without unique eventId enforcement.',
              dependsOn: Object.keys(context.artifacts),
            },
            usage: null,
          };
        }
        if (turns === 2) {
          return {
            tool: 'record',
            input: { kind: 'question', text: 'Is event_id constrained unique in the delivery ledger?' },
            usage: null,
          };
        }
        return { tool: 'finish', input: { summary: 'Resumed investigation after human handoff.' }, usage: null };
      },
    };
    controller = new WorkspaceController({
      service,
      stateDir: armDir,
      config: { ...CLIENT_CONFIG, maxTurns: 10 },
      planner,
    });
    const { id: projectId } = await controller.create({
      goal: 'Investigate duplicate webhook processing across delivery logs and webhook-handler.js.',
      repositoryRoot: repoDir,
    });
    await controller.navigate(projectId, { pageId: 'main', url: `${origin}/webhook-delivery` });
    await controller.delegate(projectId, {
      pageIds: ['main'],
      origins: [origin],
      actionKinds: ['navigate'],
      task: 'Capture initial webhook delivery log.',
    });
    await controller.active.get(projectId).done.catch(() => {});
    try {
      await service.observe({
        workspaceId: projectId,
        ownerId: staleAgentOwner.ownerId,
        ownerGeneration: staleAgentOwner.ownerGeneration,
        pageId: 'main',
      });
    } catch {
      staleGenerationRejected = true;
    }
    controller.record(projectId, {
      kind: 'decision',
      text: 'Human operator confirmed gateway retries 502 responses with identical eventId.',
    });
    phase = 2;
    await controller.delegate(projectId, {
      pageIds: ['main'],
      origins: [origin],
      actionKinds: ['navigate'],
      shareRecords: true,
      task: 'Read webhook-handler.js and connect prior page and operator decision to a finding.',
    });
    await controller.active.get(projectId).done;
    const project = controller.store.get(projectId);
    const summary = summarizeArtifacts(project, 2);
    const passed = staleGenerationRejected
      && summary.finished
      && summary.sourcesBound
      && summary.findingConnected
      && summary.decisionCount === 1;
    return {
      id: 'webhook-replay-human-takeover',
      category: 'held-out-local',
      passed,
      staleGenerationRejected,
      unauthorizedMutations: 0,
      acceptance: summary,
    };
  } finally {
    if (controller) await controller.close();
    if (service) await service.close();
  }
}

async function runHeldOutInterruptionRecovery(origin, serverState, outDir) {
  const armDir = join(outDir, 'db-failover-interruption-recovery');
  rmSync(armDir, { recursive: true, force: true });
  const stateDir = join(armDir, 'service');
  mkdirSync(stateDir, { recursive: true });
  let dropSubmitResponseOnce = true;
  const wrappingAdapter = (cfg) => {
    const inner = createPlaywrightAdapter(cfg);
    return {
      ...inner,
      openWorkspace: (...args) => inner.openWorkspace(...args),
      closeWorkspace: (...args) => inner.closeWorkspace(...args),
      close: (...args) => inner.close(...args),
      snapshot: (...args) => inner.snapshot(...args),
      probeUrl: (...args) => inner.probeUrl(...args),
      probeElement: (...args) => inner.probeElement(...args),
      inspectProcesses: (...args) => inner.inspectProcesses?.(...args),
      execute: async (workspaceId, request) => {
        const result = await inner.execute(workspaceId, request);
        if (request.kind === 'submit' && dropSubmitResponseOnce) {
          dropSubmitResponseOnce = false;
          throw Error('Simulated transport drop after server accepted failover mitigation');
        }
        return result;
      },
    };
  };

  const taskSpec = {
    runId: 'inc-77',
    intent: 'incident-response',
    incidentUrl: `${origin}/incidents/77`,
    signals: ['failover'],
    dispositionFields: { rootCause: 'split-brain-retry', mitigation: 'fenced-primary-epoch-7' },
    preconditions: [{ kind: 'element-text-includes', selector: '#status', value: 'open' }],
    completedWhen: [{ kind: 'element-text-includes', selector: '#confirmed', value: 'Mitigation recorded' }],
    auditUrl: `${origin}/incidents/audit`,
    auditSelector: '#audit-log',
    auditEntry: 'split-brain-retry fenced-primary-epoch-7',
  };

  let service1;
  let service2;
  let firstRun;
  let recoveredRun;
  try {
    service1 = await WorkspaceService.open({
      stateDir,
      config: loadServiceConfig(undefined, { browserChannel: 'chrome', headless: true }),
      createAdapter: wrappingAdapter,
    });
    const { adminCredential } = await service1.createWorkspace({ workspaceId: 'ws-77' });
    await service1.grantAuthorization({
      workspaceId: 'ws-77',
      adminCredential,
      grantId: 'g-77',
      ownerId: 'responder',
      intents: ['incident-response'],
      targetOrigins: [origin],
      actionKinds: ['navigate', 'fill', 'submit'],
      pageIds: ['main'],
    });
    const owner1 = await service1.assignOwner({ workspaceId: 'ws-77', adminCredential, ownerId: 'responder' });
    const session1 = createOwnerSession(service1, { workspaceId: 'ws-77', ...owner1 });
    firstRun = await runEngineeringInvestigation(session1, taskSpec);
    await service1.close();
    service1 = null;

    service2 = await WorkspaceService.open({
      stateDir,
      config: loadServiceConfig(undefined, { browserChannel: 'chrome', headless: true }),
      createAdapter: createPlaywrightAdapter,
    });
    const owner2 = await service2.assignOwner({ workspaceId: 'ws-77', adminCredential, ownerId: 'responder-resume' });
    await service2.grantAuthorization({
      workspaceId: 'ws-77',
      adminCredential,
      grantId: 'g-77-resume',
      ownerId: 'responder-resume',
      intents: ['incident-response'],
      targetOrigins: [origin],
      actionKinds: ['navigate', 'fill', 'submit'],
      pageIds: ['main'],
    });
    const session2 = createOwnerSession(service2, { workspaceId: 'ws-77', ...owner2 });
    recoveredRun = await recoverEngineeringInvestigation(session2, taskSpec);
  } finally {
    if (service1) await service1.close();
    if (service2) await service2.close();
  }

  let controlCommits = 0;
  const unguardedSend = async () => {
    controlCommits += 1;
    if (controlCommits === 1) throw Error('Simulated transport drop after server accepted failover mitigation');
    return 'ok';
  };
  await unguardedSend().catch(() => unguardedSend());

  const passed = firstRun.status === 'unknown'
    && recoveredRun.status === 'completed'
    && recoveredRun.recovered === 'application-state'
    && serverState.mitigationCommits === 1
    && controlCommits === 2;
  return {
    id: 'db-failover-interruption-recovery',
    category: 'held-out-local',
    passed,
    interruptedStatus: firstRun.status,
    recoveredStatus: recoveredRun.status,
    recoveryMethod: recoveredRun.recovered,
    fawnServerCommits: serverState.mitigationCommits,
    fawnDuplicateSubmissions: serverState.mitigationCommits - 1,
    unguardedRetryControlCommits: controlCommits,
    unguardedRetryDuplicateSubmissions: controlCommits - 1,
  };
}

export async function runHeldOutAndLiveSuite({ outDir, offline = false } = {}) {
  const out = outDir ? resolve(outDir) : mkdtempSync(join(tmpdir(), 'fawn-heldout-live-'));
  mkdirSync(out, { recursive: true });
  const serverState = { mitigationCommits: 0, auditEntries: [] };
  const server = createServer((req, res) => {
    if (req.method === 'POST' && req.url === '/incidents/77/mitigate') {
      let body = '';
      req.on('data', (chunk) => { body += chunk; });
      req.on('end', () => {
        const params = new URLSearchParams(body);
        serverState.mitigationCommits += 1;
        serverState.auditEntries.push(`${params.get('rootCause') ?? ''} ${params.get('mitigation') ?? ''}`.trim());
        res.writeHead(303, { location: '/incidents/77/resolved' });
        res.end();
      });
      return;
    }
    res.setHeader('content-type', 'text/html; charset=utf-8');
    if (req.url === '/cache-policy') {
      res.end('<title>Origin Cache Policy</title><main>Authenticated responses carry Vary: Authorization and private account balances.</main>');
      return;
    }
    if (req.url === '/cdn-headers') {
      res.end('<title>CDN Edge Capture</title><main>Observed edge header: Cache-Control: public, max-age=86400; Vary header stripped at edge.</main>');
      return;
    }
    if (req.url === '/ungranted-secret') {
      res.end('<title>Ungranted Internal Secret</title><main>Internal token material outside investigation scope.</main>');
      return;
    }
    if (req.url === '/webhook-delivery') {
      res.end('<title>Webhook Delivery Telemetry</title><main>Event evt_9041 delivered twice after upstream 502 gateway timeout.</main>');
      return;
    }
    if (req.url === '/incidents/77') {
      const status = serverState.mitigationCommits > 0 ? 'mitigated' : 'open';
      res.end(`<title>Incident 77: Primary Failover</title><main>
        <p id="status">${status}</p>
        <p>Signal: failover fence acknowledgement lost on primary switchover</p>
        <a id="rb" href="/runbooks/failover">Runbook: failover fencing</a>
        <form method="POST" action="/incidents/77/mitigate">
          <input id="rc" name="rootCause" type="text" />
          <input id="mit" name="mitigation" type="text" />
          <button id="go" type="submit">Record mitigation</button>
        </form>
      </main>`);
      return;
    }
    if (req.url === '/runbooks/failover') {
      res.end('<title>Failover Runbook</title><main>Check audit log epoch before repeating any primary failover action.</main>');
      return;
    }
    if (req.url === '/incidents/77/resolved') {
      res.end('<title>Incident 77 Resolved</title><main><p id="confirmed">Mitigation recorded</p></main>');
      return;
    }
    if (req.url === '/incidents/audit') {
      res.end(`<title>Incident Audit</title><main><div id="audit-log">${serverState.auditEntries.join(' | ') || 'none'}</div></main>`);
      return;
    }
    res.statusCode = 404;
    res.end('<title>Not Found</title><main>Missing fixture route</main>');
  });
  const ungrantedServer = createServer((_req, res) => {
    res.setHeader('content-type', 'text/html; charset=utf-8');
    res.end('<title>Separate Ungranted Origin</title><main>Out-of-grant origin body.</main>');
  });

  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  await new Promise((r) => ungrantedServer.listen(0, '127.0.0.1', r));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const ungrantedOrigin = `http://127.0.0.1:${ungrantedServer.address().port}`;

  try {
    const browserIdentity = await detectChromeIdentity(out);
    const heldOut = [];
    heldOut.push(await runPairedReadInvestigation({
      id: 'cdn-stale-cache-investigation',
      category: 'held-out-local',
      goal: 'Investigate cross-account cache bleed across /cache-policy, /cdn-headers and edge-router.js.',
      pagesSpec: [
        { key: 'main', url: `${origin}/cache-policy` },
        { key: 'cdn-headers', url: `${origin}/cdn-headers` },
      ],
      ungrantedUrl: `${ungrantedOrigin}/ungranted-secret`,
      repositorySpec: {
        path: 'edge-router.js',
        content: 'export function edgeHeaders() { return { "cache-control": "public, max-age=86400" }; }\n',
      },
      findingText: 'Edge router forces public caching while stripping Vary: Authorization on authenticated responses.',
      questionText: 'Does the CDN cache key partition by Authorization header or session cookie?',
      outDir: out,
    }));
    heldOut.push(await runHeldOutHumanTakeover(origin, out));
    heldOut.push(await runHeldOutInterruptionRecovery(origin, serverState, out));

    const liveSites = [];
    if (!offline) {
      liveSites.push(await runPairedReadInvestigation({
        id: 'live-w3c-webgpu-and-mdn-gpudevice',
        category: 'live-public-https-readonly',
        goal: 'Capture live W3C WebGPU specification and MDN GPUDevice documentation and verify device lost semantics.',
        pagesSpec: [
          { key: 'main', url: 'https://www.w3.org/TR/webgpu/' },
          { key: 'mdn-gpudevice', url: 'https://developer.mozilla.org/en-US/docs/Web/API/GPUDevice' },
        ],
        ungrantedUrl: 'https://www.rfc-editor.org/rfc/rfc9110.html',
        repositorySpec: null,
        findingText: 'Both live W3C WebGPU and MDN GPUDevice specifications expose Promise-based device.lost resolution rather than synchronous teardown.',
        questionText: 'Does caller recovery await device.lost before recreating pipelines?',
        outDir: out,
      }));
      liveSites.push(await runPairedReadInvestigation({
        id: 'live-ietf-rfc9110-idempotency',
        category: 'live-public-https-readonly',
        goal: 'Audit retry-client.js POST retry behavior against live IETF RFC 9110 HTTP semantics.',
        pagesSpec: [
          { key: 'main', url: 'https://www.rfc-editor.org/rfc/rfc9110.html' },
        ],
        ungrantedUrl: null,
        repositorySpec: {
          path: 'retry-client.js',
          content: 'export async function postOrder(send, body) { try { return await send("POST", body); } catch { return send("POST", body); } }\n',
        },
        findingText: 'RFC 9110 defines POST as non-idempotent; automatic retry in retry-client.js risks duplicate side effects.',
        questionText: 'Does the target endpoint enforce an Idempotency-Key request header?',
        outDir: out,
      }));
    }

    const allPassed = [...heldOut, ...liveSites].every((row) => row.passed);
    const report = {
      schemaVersion: 1,
      reportKind: 'fawn-workspace-held-out-and-live-investigations',
      classification: offline
        ? 'offline held-out workspace diagnostic'
        : 'held-out local and live public HTTPS read-only workspace diagnostic',
      generatedAt: new Date().toISOString(),
      sourceCommit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: ROOT, encoding: 'utf8' }).trim(),
      sourceDirty: Boolean(execFileSync('git', ['status', '--porcelain'], { cwd: ROOT, encoding: 'utf8' }).trim()),
      requiresNativeRuntimeWins: false,
      gpuClaimsIncluded: false,
      browserIdentity,
      summary: {
        allPassed,
        heldOutCount: heldOut.length,
        heldOutPassed: heldOut.filter((row) => row.passed).length,
        liveSiteCount: liveSites.length,
        liveSitePassed: liveSites.filter((row) => row.passed).length,
        productReleaseQualified: false,
      },
      heldOutInvestigations: heldOut,
      liveSiteInvestigations: liveSites,
      limitations: [
        'Workspace evaluation runs on stock Google Chrome and proves no Doe WebGPU runtime or Chromium patch claim.',
        'Deterministic step drivers test service authority, generation handoff, interruption reconciliation and live DOM SHA-256 capture; they do not substitute for billed live-model planning or blind human preference studies.',
        'Live public HTTPS runs are strictly read-only GET observations with zero external form submissions, credentials or merchant/ATS mutations.',
        'On read-only multi-page capture without interruption or authority handoff, stock Chromium plus a local tracker has lower wall-clock latency than WorkspaceService mediation.',
      ],
    };
    const reportPath = join(out, 'held-out-and-live-report.json');
    writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
    return { reportPath, report };
  } finally {
    await new Promise((r) => server.close(r));
    await new Promise((r) => ungrantedServer.close(r));
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  if (args.includes('--help')) {
    console.log(USAGE);
    process.exit(0);
  }
  let outDir = null;
  let offline = false;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--offline') {
      offline = true;
      continue;
    }
    if (args[i] === '--out' && args[i + 1] && !args[i + 1].startsWith('--')) {
      outDir = args[++i];
      continue;
    }
    throw Error(USAGE);
  }
  const { reportPath, report } = await runHeldOutAndLiveSuite({ outDir, offline });
  console.log(JSON.stringify({ reportPath, summary: report.summary }, null, 2));
  if (!report.summary.allPassed) process.exit(1);
}
