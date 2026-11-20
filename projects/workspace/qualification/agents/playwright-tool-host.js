#!/usr/bin/env node
// Fawn workspace differentiation — control tool host: Playwright agent tooling over stock Chromium.
//
// The Playwright MCP mechanism as a separate process that outlives the agent: page-wide agent
// snapshots with incremental tracking, and actions on aria refs from the latest snapshot.
// Usage: node playwright-tool-host.js '{"stateDir": "...", "actionTimeoutMs": n, "headless": true}'

import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { createInterface } from 'node:readline';
import { chromium } from 'playwright-core';
import { loadServiceConfig } from '../../src/config.js';
import { playwrightLaunchOptions } from '../../src/browser-launch.js';

const options = JSON.parse(process.argv[2]);
const browserConfig = loadServiceConfig(options.browserConfig ?? undefined, { browserChannel: options.browserChannel }).browser;
const SNAPSHOT_TRACK = 'agent';
// The harness keeps its own snapshot baseline, taken with each model observation, so that
// revalidation sees what changed since the model last looked without disturbing the model's track.
const REVALIDATION_TRACK = 'revalidate';
const CHANGED_REF = /<changed>[^\n]*\[ref=(e\d+)\]/g;

function emit(message) {
  process.stdout.write(`${JSON.stringify(message)}\n`);
}

mkdirSync(options.stateDir, { recursive: true });
let context = null;

async function page() {
  if (!context) {
    context = await chromium.launchPersistentContext(join(options.stateDir, 'profile'), {
      headless: options.headless,
      ...playwrightLaunchOptions(browserConfig),
      acceptDownloads: true,
      timeout: options.actionTimeoutMs,
    });
  }
  const current = context.pages()[0] ?? await context.newPage();
  current.setDefaultTimeout(options.actionTimeoutMs);
  return current;
}

const byRef = async (ref) => (await page()).locator(`aria-ref=${ref}`);

const OPERATIONS = Object.freeze({
  async snapshot() {
    const current = await page();
    const snapshot = await current._snapshotForAI({ track: SNAPSHOT_TRACK });
    return { url: current.url(), full: snapshot.full, incremental: snapshot.incremental ?? null };
  },
  async observeForModel() {
    const current = await page();
    const snapshot = await current._snapshotForAI({ track: SNAPSHOT_TRACK });
    await current._snapshotForAI({ track: REVALIDATION_TRACK });
    return { url: current.url(), full: snapshot.full, incremental: snapshot.incremental ?? null };
  },
  /**
   * Before a mutation: is the target ref still on the page, and did anything change since the
   * model's last observation inside (or around) the regions its decision named?
   */
  async revalidate({ regions, ref }) {
    const current = await page();
    if (await current.locator(`aria-ref=${ref}`).count() !== 1) return { stale: true, detail: 'the element is no longer on the page' };
    const snapshot = await current._snapshotForAI({ track: REVALIDATION_TRACK });
    if (regions.length === 0 || !snapshot.incremental) return { stale: false };
    for (const [, changedRef] of snapshot.incremental.matchAll(CHANGED_REF)) {
      const changed = await current.locator(`aria-ref=${changedRef}`).elementHandle().catch(() => null);
      if (!changed) continue;
      for (const region of regions) {
        const overlaps = await current.locator(region).evaluateAll(
          (roots, element) => roots.some((root) => root.contains(element) || element.contains(root)), changed);
        if (overlaps) return { stale: true, detail: `${region} changed: ${snapshot.incremental.slice(0, 600)}` };
      }
    }
    return { stale: false };
  },
  async select({ ref, value }) {
    await (await byRef(ref)).selectOption(value);
    return { ok: true };
  },
  async navigate({ url }) {
    const current = await page();
    await current.goto(url, { waitUntil: 'load' });
    return { url: current.url() };
  },
  async click({ ref }) {
    await (await byRef(ref)).click();
    return { url: (await page()).url() };
  },
  async fill({ ref, value }) {
    await (await byRef(ref)).fill(value);
    return { ok: true };
  },
  async formAction() {
    return { action: await (await page()).evaluate(() => document.querySelector('form')?.action ?? null) };
  },
  async download({ ref }) {
    const current = await page();
    const [download] = await Promise.all([current.waitForEvent('download'), (await byRef(ref)).click()]);
    const path = join(options.stateDir, `download-${Date.now()}-${download.suggestedFilename()}`);
    await download.saveAs(path);
    return { sha256: createHash('sha256').update(readFileSync(path)).digest('hex') };
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
