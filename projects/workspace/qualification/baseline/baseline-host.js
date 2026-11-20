#!/usr/bin/env node
// Fawn workspace comparison — baseline host driven over stdin/stdout JSON lines, like the
// service host, so both sides pay the same process and IPC costs and can be killed the same way.
// Usage: node baseline-host.js '{"stateDir": "...", "allowedOrigins": [...], "actionTimeoutMs": n, "headless": true}'

import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { createInterface } from 'node:readline';
import { chromium } from 'playwright-core';
import { BASELINE_WORKFLOWS, ProgressFile } from './baseline-workflows.js';
import { loadServiceConfig } from '../../src/config.js';
import { playwrightLaunchOptions } from '../../src/browser-launch.js';

const options = JSON.parse(process.argv[2]);
const browserConfig = loadServiceConfig(options.browserConfig ?? undefined, { browserChannel: options.browserChannel }).browser;
const PROFILE_DIRECTORY = 'profile';
const PROGRESS_FILE = 'progress.json';

function emit(message) {
  process.stdout.write(`${JSON.stringify(message)}\n`);
}

mkdirSync(options.stateDir, { recursive: true });
const progress = new ProgressFile(join(options.stateDir, PROGRESS_FILE));
let context = null;

async function page() {
  if (!context) {
    context = await chromium.launchPersistentContext(join(options.stateDir, PROFILE_DIRECTORY), {
      ...playwrightLaunchOptions(browserConfig),
      headless: options.headless,
      acceptDownloads: true,
      timeout: options.actionTimeoutMs,
    });
  }
  const current = context.pages()[0] ?? await context.newPage();
  current.setDefaultTimeout(options.actionTimeoutMs);
  return current;
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const OPERATIONS = Object.freeze({
  async workflow({ name, task, beforeEffect }) {
    let observationBytes = 0;
    const env = {
      page: await page(),
      progress,
      allowedOrigins: options.allowedOrigins,
      artifactDir: join(options.stateDir, 'artifacts'),
      async read(reader) {
        const value = await reader();
        observationBytes += Buffer.byteLength(JSON.stringify(value ?? null));
        return value;
      },
      async beforeEffect() {
        if (!beforeEffect) return;
        if (beforeEffect.controlUrl) await fetch(beforeEffect.controlUrl);
        await sleep(beforeEffect.settleMs);
      },
    };
    const result = await BASELINE_WORKFLOWS[name](env, task);
    return { result, observationBytes };
  },
  async close() {
    await context?.close();
    setImmediate(() => process.exit(0));
    return null;
  },
});

emit({ event: 'ready', pid: process.pid });
for await (const line of createInterface({ input: process.stdin })) {
  const { id, op, args } = JSON.parse(line);
  Promise.resolve()
    .then(() => OPERATIONS[op](args))
    .then((result) => emit({ id, ok: true, result }), (error) => emit({ id, ok: false, error: { code: error.code ?? null, message: error.message } }));
}
await context?.close();
process.exit(0);
