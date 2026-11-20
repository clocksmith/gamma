#!/usr/bin/env node
// Probe only an explicitly selected binary in a new isolated profile.
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { chromium } from 'playwright-core';
import { inspectBeginFrame } from '../support/headless-render-control.js';

const options = {};
for (let index = 2; index < process.argv.length; index += 2) {
  const key = process.argv[index];
  if (!['--executable', '--out'].includes(key) || !process.argv[index + 1] || options[key]) {
    throw Error('usage: headless-render-control.js --executable BINARY --out NEW_DIRECTORY');
  }
  options[key] = process.argv[index + 1];
}
if (!options['--executable'] || !options['--out']) throw Error('explicit binary and new output directory required');
const executable = realpathSync(options['--executable']);
const output = resolve(options['--out']);
mkdirSync(output, { recursive: false });
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const controlFlags = ['--enable-begin-frame-control', '--run-all-compositor-stages-before-draw'];
const receipt = {
  schemaVersion: 1, classification: 'diagnostic capability probe; not render-on-demand qualification',
  observedAt: new Date().toISOString(), executable: { path: executable, sha256: sha256(readFileSync(executable)) },
  requestedFlags: ['--headless', ...controlFlags], transport: 'isolated Playwright CDP pipe',
  status: 'not-run', limitations: ['An available method does not establish frame cadence, application readiness or presentation correctness.'],
};
let context;
try {
  context = await chromium.launchPersistentContext(join(output, 'profile'), {
    executablePath: executable, headless: true, args: controlFlags, timeout: 30000,
  });
  const page = context.pages()[0] ?? await context.newPage();
  await page.goto('data:text/html,<title>Isolated render-control probe</title><canvas width="8" height="8"></canvas>');
  const session = await context.newCDPSession(page);
  receipt.browser = await session.send('Browser.getVersion');
  receipt.commandLine = await session.send('Browser.getBrowserCommandLine');
  const result = await inspectBeginFrame((method, params) => session.send(method, params));
  receipt.status = result.status;
  receipt.reason = result.reason ?? null;
  receipt.hasDamage = result.hasDamage ?? null;
  if (result.screenshot) {
    writeFileSync(join(output, 'frame.png'), result.screenshot);
    receipt.screenshot = { bytes: result.screenshot.length, sha256: sha256(result.screenshot) };
  }
} catch (error) {
  receipt.status = 'failed';
  receipt.error = error.message;
  process.exitCode = 1;
} finally {
  if (context) {
    try { await context.close(); receipt.browserClosed = true; }
    catch (error) { receipt.status = 'failed'; receipt.closeError = error.message; process.exitCode = 1; }
  }
  writeFileSync(join(output, 'result.json'), JSON.stringify(receipt, null, 2) + '\n');
  console.log(JSON.stringify({ status: receipt.status, reason: receipt.reason, browser: receipt.browser?.product, output }));
}
