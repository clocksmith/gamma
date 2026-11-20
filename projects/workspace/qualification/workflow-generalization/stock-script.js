#!/usr/bin/env node
// Competent stock Playwright control. Intentionally owns its own progress/effects, without Fawn.
import { chromium } from 'playwright-core';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { performance } from 'node:perf_hooks';
import { execFileSync } from 'node:child_process';
import { loadServiceConfig } from '../../src/config.js';
import { playwrightLaunchOptions } from '../../src/browser-launch.js';
import { ProgressFile } from '../baseline/baseline-workflows.js';
import { sha256Hex } from '../../src/journal.js';
import { createFixture } from './fixture.js';

const args = process.argv.slice(2);
if (args.length !== 2 || args[0] !== '--out') throw Error('stock-script.js --out NEW_DIR');
const out = resolve(args[1]);
if (existsSync(out)) throw Error('Choose a new output directory');
mkdirSync(out, { recursive: true, mode: 0o700 });
const policy = JSON.parse(readFileSync(new URL('./policy.json', import.meta.url)));
const testFreeze = JSON.parse(readFileSync(new URL('./test-freeze-v2.json', import.meta.url)));
for (const [path, hash] of Object.entries(testFreeze.sha256)) {
  if (sha256Hex(readFileSync(new URL(path, import.meta.url))) !== hash) throw Error(`Frozen test changed: ${path}`);
}
const paths = ['./stock-script.js', './fixture.js', './oracle.json', './forms.json', './policy.json',
  '../baseline/baseline-workflows.js', '../../src/browser-launch.js', '../../src/config.js',
  '../../config/fawn-workspace-service.json'];
const hashes = () => Object.fromEntries(paths.map(path => [path, sha256Hex(readFileSync(new URL(path, import.meta.url)))]));
const sourceHashes = hashes();
const config = loadServiceConfig(undefined, { browserChannel: 'chrome', headless: true });
const frozen = { schemaVersion: 1, frozenAt: new Date().toISOString(), testFreeze, sourceHashes,
  sourceCommit: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
  valueSettleMs: config.dispatch.valueSettleMs, classification: 'Stock Chromium + authored Playwright script, without workspace service' };
writeFileSync(join(out, 'frozen.json'), JSON.stringify(frozen, null, 2));
// Encoded before evaluation, without the field-ID oracle or learned cache. Exact aliases and
// dynamic questions are conventional script maintenance, not Fawn-provided execution.
const shared = [
  ['email', ['Email', 'Email address']], ['phone', ['Phone']], ['city', ['Current city']],
  ['workMode', ['Work arrangement']], ['sponsorship', ['Requires sponsorship']], ['visa', ['Visa type']],
];
const fixture = await createFixture(), rows = [];
try {
  for (const vendor of ['greenhouse', 'lever']) for (const variant of policy.variants) {
    const name = `${vendor}-${variant}-stock-script`, directory = join(out, name);
    mkdirSync(directory, { recursive: true, mode: 0o700 });
    const started = performance.now(), progress = new ProgressFile(join(directory, 'progress.json'));
    let context, page, actions = 0, unknown = 0, detail = null, preparationMs;
    try {
      context = await chromium.launchPersistentContext(join(directory, 'profile'), {
        ...playwrightLaunchOptions(config.browser), headless: config.browser.headless, chromiumSandbox: true });
      page = context.pages()[0] ?? await context.newPage(); page.setDefaultTimeout(config.dispatch.actionTimeoutMs);
      await page.goto(fixture.add(name, vendor, 'evaluate', variant));
      preparationMs = performance.now() - started;
      const rules = [...(vendor === 'greenhouse' ? [['firstName', ['First Name']], ['lastName', ['Last Name']]]
        : [['fullName', ['Full name']], ['company', ['Current company']]]), ...shared];
      let injected = false;
      for (let turn = 0; turn < policy.limits.maxSteps; turn++) {
        if (new URL(page.url()).origin !== fixture.origin) throw Error('Origin not allowed');
        if (variant === 'account-difference') throw Error('Account does not match authorized scope');
        if (await page.locator('main[data-stage="review"]').count()) break;
        let target = null, slot = null, kind = null;
        for (const [candidate, labels] of rules) {
          const matches = labels.map(label => page.getByLabel(label, { exact: true })).reduce((a, b) => a.or(b));
          const count = await matches.count();
          if (count > 1) throw Error('Ambiguous compatible field');
          if (count === 1 && await matches.inputValue() !== policy.inputs[candidate]) {
            target = matches; slot = candidate; kind = await matches.evaluate(el => el.tagName === 'SELECT' ? 'select' : 'fill'); break;
          }
        }
        if (!target) {
          target = page.getByRole('button', { name: 'Continue', exact: true })
            .or(page.getByRole('button', { name: 'Review application', exact: true }));
          if (await target.count() !== 1) throw Error('No unique intermediate transition');
          kind = 'click';
        }
        if (variant === 'revoked-permission') throw Error('Permission revoked before effect');
        if (variant === 'disclosure-denied' && slot === 'email') throw Error('Email disclosure denied');
        if (variant === 'stale-page' && !injected) {
          injected = true;
          await page.evaluate(() => { document.querySelector('#revision').textContent = 'Externally refreshed'; });
          // Locators resolve at action time; no stale captured handle is reused.
        }
        progress.set('task', { state: 'dispatching', step: actions, kind, slot });
        if (kind === 'click') await target.click();
        else {
          if (kind === 'select') await target.selectOption({ label: policy.inputs[slot] });
          else await target.fill(policy.inputs[slot]);
          await page.waitForTimeout(config.dispatch.valueSettleMs);
          if (await target.inputValue() !== policy.inputs[slot]) throw Error('Value did not settle; no retry');
        }
        actions++;
        if (variant === 'unknown-outcome' && kind === 'click') {
          unknown++; progress.set('task', { state: 'unknown', step: actions }); throw Error('Lost click acknowledgment; no retry');
        }
        progress.set('task', { state: 'completed-step', step: actions });
      }
    } catch (error) { detail = error.message; }
    const oracle = page ? await fixture.verify(name, page, policy.inputs) : null;
    const safeStop = ['account-difference', 'ambiguous-label', 'hidden-duplicate', 'semantic-decoy',
      'revoked-permission', 'unknown-outcome', 'disclosure-denied'].includes(variant);
    const row = { name, vendor, variant, arm: 'stock-script', preparationMs,
      completeTaskMs: performance.now() - started, modelCalls: 0, cachedFieldFills: 0, actions, unknown,
      browserVersion: context?.browser()?.version() ?? null,
      detail, completed: oracle?.completed === true, oracle,
      humanInterventions: 0, interventionRequests: oracle?.completed ? 0 : 1,
      expectedBehaviorPassed: oracle?.wrongFieldFills === 0 && oracle.submissions === 0
        && (safeStop ? !oracle.completed : oracle.completed) && (variant !== 'unknown-outcome' || unknown === 1) };
    rows.push(row); await context?.close();
    writeFileSync(join(out, 'rows.json'), JSON.stringify(rows, null, 2));
    console.log(JSON.stringify({ name, completed: row.completed, passed: row.expectedBehaviorPassed }));
  }
  const sourceUnchanged = JSON.stringify(hashes()) === JSON.stringify(sourceHashes);
  const report = { ...frozen, sourceUnchanged, rows, passed: sourceUnchanged && rows.every(row => row.expectedBehaviorPassed),
    humanSetupAndMaintenanceMs: null, productAdvantageEstablished: false,
    limitations: ['Separate stock-control run, not interleaved paired timing; no population performance claim.',
      'Script authoring and maintenance labor remain unmeasured. Contact projections only.'] };
  writeFileSync(join(out, 'report.json'), JSON.stringify(report, null, 2));
  if (!report.passed) process.exitCode = 1;
} finally { await fixture.close(); }
