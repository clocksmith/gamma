// Retained browser WebGPU worker with the same JSONL contract as the Node worker.
import { readFile, realpath } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { createInterface } from 'node:readline';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

console.log = console.error;
console.info = console.error;
const config = JSON.parse(await readFile(process.argv[2], 'utf8'));
const root = await realpath(config.root);
const require = createRequire(path.join(root, 'package.json'));
const { chromium } = require('playwright');
const { createStaticFileServer } = await import(pathToFileURL(path.join(root, 'src/tooling/node-browser-command-runner.js')));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const core = await readFile(new URL('./doppler_session.mjs', import.meta.url), 'utf8');
const specs = {};
for (const role of ['embedding', 'rerank']) {
  if (!config[role]) continue;
  const spec = config[role];
  const location = await realpath(spec.path);
  if (!location.startsWith(root + path.sep)) throw new Error('Browser models must be provisioned inside Doppler');
  const bytes = await readFile(path.join(location, 'manifest.json'));
  if (hash(bytes) !== spec.manifest_sha256) throw new Error('Model manifest changed');
  specs[role] = { ...spec, url: '/' + path.relative(root, location).split(path.sep).map(encodeURIComponent).join('/') };
}

let server, browser, page;
try {
  server = await createStaticFileServer({ rootDir: root, host: '127.0.0.1', port: 0 });
  const args = ['--enable-unsafe-webgpu', '--enable-webgpu-developer-features',
    '--disable-dawn-features=disallow_unsafe_apis', '--ignore-gpu-blocklist'];
  if (process.platform === 'linux') args.push('--use-angle=vulkan', '--enable-features=Vulkan', '--disable-vulkan-surface');
  if (process.platform === 'darwin') args.push('--use-angle=metal');
  browser = await chromium.launch({ channel: config.browser_channel || 'chrome', headless: true, args });
  page = await browser.newPage();
  page.on('console', message => console.error(`[browser:${message.type()}] ${message.text()}`));
  page.on('pageerror', error => console.error(error.stack));
  // All model/kernel requests stay on the loopback server. No external model fetch.
  await page.route('**/*', route => new URL(route.request().url()).origin === new URL(server.baseUrl).origin
    ? route.continue() : route.abort());
  await page.goto(server.baseUrl, { waitUntil: 'domcontentloaded' });
  await page.evaluate(async ({ core, specs, maxTokens }) => {
    const adapter = await navigator.gpu?.requestAdapter({ powerPreference: 'high-performance' });
    if (!adapter) throw new Error('Browser WebGPU adapter unavailable');
    const info = adapter.info ?? await adapter.requestAdapterInfo?.() ?? {};
    const identity = [info.vendor, info.architecture, info.device, info.description].join(' ').toLowerCase();
    if (adapter.isFallbackAdapter || info.isFallbackAdapter || /swiftshader|llvmpipe|software rasterizer/.test(identity)) {
      throw new Error('Physical browser GPU required');
    }
    const coreUrl = URL.createObjectURL(new Blob([core], { type: 'text/javascript' }));
    const { createRecognitionSession } = await import(coreUrl);
    URL.revokeObjectURL(coreUrl);
    const { load } = await import('/src/client/doppler-api.js');
    globalThis.gammaRecognition = createRecognitionSession({ maxTokens, loadModel: async role => {
      const spec = specs[role];
      if (!spec) throw new Error(`No ${role} model configured`);
      const response = await fetch(spec.url + '/manifest.json');
      if (!response.ok) throw new Error('Browser manifest unavailable');
      const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', await response.arrayBuffer())))
        .map(x => x.toString(16).padStart(2, '0')).join('');
      if (digest !== spec.manifest_sha256) throw new Error('Browser manifest hash mismatch');
      return load({ url: new URL(spec.url, location.href).href }, {
        cache: false, isolatedLoader: true, runtimeConfig: spec.runtime_config ?? {}, onProgress() {},
      });
    }});
  }, { core, specs, maxTokens: config.max_tokens });

  for await (const line of createInterface({ input: process.stdin, crlfDelay: Infinity })) {
    let request;
    try {
      request = JSON.parse(line);
      if (!Number.isSafeInteger(request.id)) throw new Error('Request id required');
      const result = await page.evaluate(request => globalThis.gammaRecognition.request(request), request);
      result.input_sha256 = hash(JSON.stringify(request));
      result.execution_surface = { kind: 'browser', version: browser.version() };
      process.stdout.write(JSON.stringify({ id: request.id, ok: true, result }) + '\n');
    } catch (error) {
      process.stdout.write(JSON.stringify({ id: request?.id ?? null, ok: false, error: String(error.stack ?? error) }) + '\n');
      process.exitCode = 1;
      break;
    }
  }
} finally {
  try { if (page && !page.isClosed()) await page.evaluate(() => globalThis.gammaRecognition?.close()); }
  finally {
    try { await browser?.close(); }
    finally { await server?.close(); }
  }
}
