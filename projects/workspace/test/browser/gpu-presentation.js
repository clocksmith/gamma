#!/usr/bin/env node
// A compositor control, independent of GPU texture readback and workspace recovery.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
import { loadServiceConfig } from '../../src/config.js';
import { prepareFawnLaunch, playwrightLaunchOptions } from '../../src/browser-launch.js';
import { inspectBrowserProcesses, resultIdentity, sha256File, waitForProfileRelease } from '../../qualification/identity.js';
import { extractRenderShaders, presentationReceipt } from '../support/gpu-presentation-oracle.js';

const options = {};
for (let index = 2; index < process.argv.length; index += 2) {
  const key = process.argv[index];
  if (!['--browser-config', '--out', '--negative-control'].includes(key) || !process.argv[index + 1] || options[key]) {
    throw new Error('usage: gpu-presentation.js --browser-config PROFILE --out NEW_DIRECTORY [--negative-control omit-draw|swap-red-blue]');
  }
  options[key] = process.argv[index + 1];
}
if (!options['--browser-config'] || !options['--out']) throw new Error('explicit image profile and new output required');
if (options['--negative-control'] && !['omit-draw', 'swap-red-blue'].includes(options['--negative-control'])) throw new Error('unknown negative control');
const output = resolve(options['--out']);
mkdirSync(output, { recursive: false });
const config = loadServiceConfig(resolve(options['--browser-config']));
const launch = prepareFawnLaunch(config.browser);
if (!launch) throw new Error('explicit Fawn image profile required');
const fixturePath = fileURLToPath(new URL('../fixtures/gpu-composition.html', import.meta.url));
const fixture = readFileSync(fixturePath, 'utf8');
const shaders = extractRenderShaders(fixture);
writeFileSync(join(output, 'original-gpu-composition.html'), fixture);
writeFileSync(join(output, 'browser-profile.json'), readFileSync(resolve(options['--browser-config'])));
writeFileSync(join(output, 'executed-runner.js'), readFileSync(fileURLToPath(import.meta.url)));
writeFileSync(join(output, 'executed-oracle.js'), readFileSync(fileURLToPath(new URL('../support/gpu-presentation-oracle.js', import.meta.url))));
for (const stage of ['vertex', 'fragment']) writeFileSync(join(output, `${stage}.wgsl`), shaders[stage]);
const html = '<!doctype html><meta charset="utf-8"><style>body{margin:0;background:red}canvas{display:block;width:8px;height:8px}</style><canvas id="canvas" width="8" height="8"></canvas>';
writeFileSync(join(output, 'presentation.html'), html);
const server = createServer((_request, response) => {
  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  response.end(html);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const profile = join(output, 'profile');
const result = { scope: 'Development compositor-visible PNG pixels; no physical display scanout, timing or release qualification',
  identity: resultIdentity(), selectedBuild: launch.identity, fixtureSha256: sha256File(fixturePath),
  runnerSha256: sha256File(fileURLToPath(import.meta.url)),
  oracleSha256: sha256File(fileURLToPath(new URL('../support/gpu-presentation-oracle.js', import.meta.url))),
  shaders: Object.fromEntries(Object.entries(shaders).map(([stage, source]) => [stage, createHash('sha256').update(source).digest('hex')])),
  headless: config.browser.headless, negativeControl: options['--negative-control'] ?? null,
  observations: [], submissions: [], errors: [], gpuCompletion: 'not-dispatched', passed: false };
let context;
let page;
let initialized = false;
let finished = false;
async function bounded(promise, label, limit = 30000) {
  let timer;
  try {
    return await Promise.race([promise, new Promise((_resolve, reject) => {
      timer = setTimeout(() => reject(new Error(`${label} exceeded ${limit}ms; completion unknown`)), limit);
    })]);
  } finally { clearTimeout(timer); }
}
async function capture(name, rgba, submission = null) {
  const png = await bounded(page.locator('#canvas').screenshot({ type: 'png', animations: 'disabled' }), `${name} compositor screenshot`);
  writeFileSync(join(output, `${name}.png`), png);
  result.observations.push({ name, ...presentationReceipt(png, rgba, submission) });
}
try {
  context = await chromium.launchPersistentContext(profile, { ...playwrightLaunchOptions(config.browser),
    headless: config.browser.headless, viewport: { width: 64, height: 64 }, deviceScaleFactor: 1, timeout: 30000 });
  page = context.pages()[0] ?? await context.newPage();
  page.on('pageerror', error => result.errors.push(String(error.stack ?? error)));
  page.on('console', message => { if (message.type() === 'error') result.errors.push(`console: ${message.text()}`); });
  await page.goto(`http://127.0.0.1:${server.address().port}/`, { waitUntil: 'load', timeout: 30000 });
  await page.bringToFront();
  await capture('before-gpu-red', [255, 0, 0, 255]);
  result.gpuCompletion = 'unknown';
  result.adapter = await bounded(page.evaluate(async shaders => {
    if (!navigator.gpu) throw new Error('WebGPU unavailable');
    const adapter = await navigator.gpu.requestAdapter({ forceFallbackAdapter: false });
    if (!adapter || adapter.info.isFallbackAdapter === true) throw new Error('physical adapter required');
    const device = await adapter.requestDevice();
    window.gpuErrors = [];
    device.addEventListener('uncapturederror', event => window.gpuErrors.push(event.error.message));
    device.pushErrorScope('validation');
    const canvas = document.querySelector('#canvas');
    const context = canvas.getContext('webgpu');
    const format = navigator.gpu.getPreferredCanvasFormat();
    context.configure({ device, format, alphaMode: 'opaque' });
    const pipeline = device.createRenderPipeline({ layout: 'auto',
      vertex: { module: device.createShaderModule({ code: shaders.vertex }), entryPoint: 'main' },
      fragment: { module: device.createShaderModule({ code: shaders.fragment }), entryPoint: 'main', targets: [{ format }] } });
    const setupError = await device.popErrorScope();
    if (setupError) throw new Error(setupError.message);
    let sequence = 0;
    window.present = async ({ draw, clearValue }) => {
      device.pushErrorScope('validation');
      const encoder = device.createCommandEncoder();
      const pass = encoder.beginRenderPass({ colorAttachments: [{ view: context.getCurrentTexture().createView(),
        loadOp: 'clear', storeOp: 'store', clearValue }] });
      if (draw) { pass.setPipeline(pipeline); pass.draw(3); }
      pass.end();
      device.queue.submit([encoder.finish()]);
      await device.queue.onSubmittedWorkDone();
      const error = await device.popErrorScope();
      if (error) throw new Error(error.message);
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      return { queueCompleted: true, sequence: ++sequence, frames: 2 };
    };
    window.finish = async () => {
      await device.queue.onSubmittedWorkDone();
      context.unconfigure();
      device.destroy();
      return { queueCompleted: true, contextUnconfigured: true, deviceDestroyed: true };
    };
    return { vendor: adapter.info.vendor, architecture: adapter.info.architecture,
      device: adapter.info.device, description: adapter.info.description, isFallbackAdapter: adapter.info.isFallbackAdapter ?? null, format };
  }, shaders), 'WebGPU setup');
  initialized = true;
  for (const [name, draw, rgba] of [['gpu-clear-blue', false, [0, 0, 255, 255]],
    ['gpu-clear-magenta', false, [255, 0, 255, 255]], ['gpu-triangle-green', true, [0, 255, 0, 255]]]) {
    result.gpuCompletion = 'unknown';
    const selectedDraw = draw && options['--negative-control'] !== 'omit-draw';
    const clearValue = name === 'gpu-clear-blue'
      ? (options['--negative-control'] === 'swap-red-blue' ? { r: 1, g: 0, b: 0, a: 1 } : { r: 0, g: 0, b: 1, a: 1 })
      : { r: 1, g: 0, b: 1, a: 1 };
    const work = await bounded(page.evaluate(work => window.present(work), { draw: selectedDraw, clearValue }), name);
    assert.equal(work.queueCompleted, true);
    result.gpuCompletion = 'completed';
    assert.equal(work.sequence, result.submissions.length + 1);
    result.submissions.push({ name, ...work });
    await capture(name, rgba, work);
  }
  result.inspection = inspectBrowserProcesses(process.pid, profile);
  assert.ok(result.inspection.executables.every(image => image.sha256 === launch.identity.executable.sha256));
  assert.equal(result.inspection.listeningTcpSockets, 0);
  assert.equal(result.inspection.devToolsActivePortFiles, 0);
  if (launch.identity.runtime === 'doe-c') {
    assert.ok(result.inspection.mappedCodeModules.some(image => image.sha256 === launch.identity.library.sha256
      && image.processes.length > 0), 'selected C must be mapped in the verified owned process tree');
  }
  assert.deepEqual(result.errors, []);
  result.gpuErrors = await page.evaluate(() => window.gpuErrors);
  assert.deepEqual(result.gpuErrors, []);
  result.cleanup = await bounded(page.evaluate(() => window.finish()), 'configured context cleanup');
  finished = true;
  assert.equal(result.cleanup.queueCompleted, true);
  result.gpuCompletion = 'completed';
  prepareFawnLaunch(config.browser); // closure hashes must remain identical after execution
  result.passed = true;
} catch (error) {
  result.error = String(error.stack ?? error);
  process.exitCode = 1;
} finally {
  if (context && !result.inspection) {
    try { result.inspection = inspectBrowserProcesses(process.pid, profile); }
    catch (error) { result.inspectionError = String(error.stack ?? error); }
  }
  try {
    if (initialized && !finished && result.gpuCompletion === 'completed' && !page.isClosed()) {
      result.failureCleanup = await bounded(page.evaluate(() => window.finish()), 'failed control context cleanup', 5000);
    }
    if (context) await bounded(context.close(), 'browser close', 15000);
    await waitForProfileRelease(output);
  } catch (error) {
    result.passed = false;
    result.closeError = String(error.stack ?? error);
    process.exitCode = 1;
  }
  await new Promise(resolve => server.close(resolve));
  writeFileSync(join(output, 'result.json'), `${JSON.stringify(result, null, 2)}\n`);
  console.log(JSON.stringify({ passed: result.passed, gpuCompletion: result.gpuCompletion, output, error: result.error, closeError: result.closeError }));
}
