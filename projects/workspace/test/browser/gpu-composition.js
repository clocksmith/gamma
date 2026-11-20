#!/usr/bin/env node
// Focused integration control, separate from frozen qualification/performance campaigns.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { prepareFawnLaunch } from '../../src/browser-launch.js';
import { createOwnerSession, findElement } from '../../src/workflows/owner-session.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { createCdpAdapter } from '../../src/adapters/cdp-adapter.js';
import { inspectBrowserProcesses, resultIdentity, sha256File, waitForProfileRelease } from '../../qualification/identity.js';
import { assertGpuReport } from '../support/gpu-composition-oracle.js';
import { createGpuEvidence } from '../support/gpu-evidence.js';

const options = {};
for (let index = 2; index < process.argv.length; index += 2) {
  const flag = process.argv[index];
  if (!['--browser-config', '--out'].includes(flag) || !process.argv[index + 1] || options[flag]) {
    throw new Error('usage: gpu-composition.js --browser-config PROFILE --out NEW_DIRECTORY');
  }
  options[flag] = process.argv[index + 1];
}
if (!options['--browser-config'] || !options['--out']) throw new Error('explicit profile and fresh output directory required');
const output = resolve(options['--out']);
mkdirSync(output, { recursive: false });
const profile = resolve(options['--browser-config']);
const config = loadServiceConfig(profile);
const launch = prepareFawnLaunch(config.browser);
if (!launch) throw new Error('this control requires an explicit Fawn image profile');
writeFileSync(join(output, 'browser-profile.json'), readFileSync(profile));
const fixture = fileURLToPath(new URL('../fixtures/gpu-composition.html', import.meta.url));
writeFileSync(join(output, 'gpu-composition.html'), readFileSync(fixture));
const result = { scope: 'development GPU/workspace composition; no performance or release qualification',
  identity: resultIdentity(), selectedBuild: launch.identity, fixtureSha256: sha256File(fixture),
  oracleSha256: sha256File(fileURLToPath(new URL('../support/gpu-composition-oracle.js', import.meta.url))),
  providerEvidence: 'Explicit selection and OS module mapping; missing-C browser controls remain separately required.',
  runnerSha256: sha256File(fileURLToPath(import.meta.url)),
  evidenceWriterSha256: sha256File(fileURLToPath(new URL('../support/gpu-evidence.js', import.meta.url))),
  runs: [], status: 'running', passed: false };
const evidence = createGpuEvidence(output, result);
evidence.checkpoint('initialized');
try {
  for (const [name, factory] of [['playwright', createPlaywrightAdapter], ['cdp', createCdpAdapter]]) {
    const reports = [];
    const server = createServer(async (request, response) => {
      if (request.method === 'GET' && request.url === '/') {
        response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        response.end(readFileSync(fixture));
      } else if (request.method === 'POST' && request.url === '/report') {
        try {
          const chunks = [];
          let byteLength = 0;
          for await (const chunk of request) {
            byteLength += chunk.length;
            if (byteLength > 65536) throw new Error('oversized report');
            chunks.push(chunk);
          }
          const report = evidence.receive(name, Buffer.concat(chunks));
          reports.push(report);
          if (report.queueCompleted === true) run.gpuCompletion = 'completed';
          evidence.checkpoint('page-report-recorded', name);
          response.end('recorded');
        } catch { response.writeHead(400); response.end(); }
      } else { response.writeHead(404); response.end(); }
    });
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    const origin = `http://127.0.0.1:${server.address().port}`;
    const stateDir = join(output, name);
    const run = { adapter: name, passed: false, gpuCompletion: 'not-dispatched', reports, inspections: [] };
    result.runs.push(run);
    evidence.checkpoint('adapter-start', name);
    let service;
    const open = () => WorkspaceService.open({ stateDir, config, createAdapter: factory });
    try {
      service = await open();
      const workspaceId = 'gpu-composition';
      const { adminCredential } = await service.createWorkspace({ workspaceId });
      await service.grantAuthorization({ workspaceId, adminCredential, grantId: 'gpu-grant', ownerId: 'gpu-owner',
        intents: ['gpu:run'], actionKinds: ['navigate', 'click'], targetOrigins: [origin] });
      const owner = await service.assignOwner({ workspaceId, adminCredential, ownerId: 'gpu-owner' });
      const identity = { workspaceId, ...owner };
      let session = createOwnerSession(service, identity);
      const navigated = await session.act(await session.observe(), { actionId: 'open', authorizedIntent: 'gpu:run',
        kind: 'navigate', target: { url: `${origin}/` } });
      run.navigation = navigated;
      evidence.checkpoint('navigated', name);
      assert.equal(navigated.outcome, 'completed');
      const observation = await session.observe();
      run.gpuCompletion = 'unknown';
      evidence.checkpoint('gpu-dispatch', name);
      run.action = await session.act(observation, { actionId: 'run-gpu', authorizedIntent: 'gpu:run', kind: 'click',
        target: findElement(observation, value => value.selector === '#run', 'GPU run button'),
        completion: { completedWhen: [{ kind: 'element-present', selector: '#completed' }],
          failedWhen: [{ kind: 'element-present', selector: '#failed' }] } });
      if (reports.length === 1 && reports[0].queueCompleted === true) run.gpuCompletion = 'completed';
      evidence.checkpoint('gpu-action-returned', name);
      try { run.postActionObservation = await session.observe(); }
      catch (error) { run.postActionObservationError = String(error.stack ?? error); }
      evidence.checkpoint('post-action-dom-observed', name);
      assert.equal(run.action.outcome, 'completed', JSON.stringify({ action: run.action, reports }));
      assert.equal(reports.length, 1);
      assertGpuReport(reports[0]);
      const inspection = inspectBrowserProcesses(process.pid, join(stateDir, 'profiles'));
      run.inspections.push(inspection);
      evidence.checkpoint('process-identity-observed', name);
      assert.ok(inspection.executables.length > 0);
      assert.ok(inspection.executables.every(value => value.sha256 === launch.identity.executable.sha256));
      assert.equal(inspection.listeningTcpSockets, 0);
      assert.equal(inspection.devToolsActivePortFiles, 0);
      if (launch.identity.runtime === 'doe-c') {
        assert.ok(inspection.mappedCodeModules.some(value => value.sha256 === launch.identity.library.sha256),
          'selected C runtime must be observed mapped in the owned browser process tree');
      }
      await service.close();
      service = null;
      await waitForProfileRelease(stateDir);
      service = await open();
      session = createOwnerSession(service, identity);
      run.afterRestart = await session.action('run-gpu');
      assert.equal(run.afterRestart.outcome, 'completed');
      await session.acknowledge('run-gpu');
      assert.equal(reports.length, 1, 'restart must not resubmit GPU work');
      run.passed = true;
      evidence.checkpoint('adapter-passed', name);
    } catch (error) {
      run.error = String(error.stack ?? error);
      evidence.checkpoint('adapter-failed', name);
      throw error;
    } finally {
      try {
        await service?.close();
        await waitForProfileRelease(stateDir);
      } finally {
        await new Promise(resolve => server.close(resolve));
        evidence.checkpoint('adapter-closed', name);
      }
    }
  }
  result.passed = true;
  result.status = 'passed';
} catch (error) {
  result.status = 'failed';
  result.error = String(error.stack ?? error);
  process.exitCode = 1;
} finally {
  evidence.checkpoint('finished');
  console.log(JSON.stringify({ passed: result.passed, runtime: launch.identity.runtime, output, error: result.error }));
}
