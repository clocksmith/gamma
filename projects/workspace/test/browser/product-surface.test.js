// Real browser UI + real workspace service. The controlled planner is a test port, not model-quality evidence.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { chromium } from 'playwright-core';
import { openWorkspaceApp } from '../../src/client/main.js';
import { playwrightLaunchOptions } from '../../src/browser-launch.js';
import { testBrowserSelection } from '../support/browser-selection.js';
const directory = mkdtempSync(join(tmpdir(), 'fawn-product-surface-'));
const selected = testBrowserSelection(directory);
const config = JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url)));
let submissions = 0;
const fixture = createServer((req, res) => {
  res.setHeader('content-type', 'text/html');
  if (req.url === '/submit') { submissions++; res.end('<title>Receipt</title><h1 id="receipt">Receipt accepted</h1>'); }
  else res.end('<title>Checkout investigation</title><main id="article"><h1>Checkout regression</h1><p>Retrying an unknown request can create a duplicate order.</p><form method="post" action="/submit"><button id="send">Submit once</button></form></main>');
});
await new Promise(resolve => fixture.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${fixture.address().port}`;
const gate = Promise.withResolvers();
let turn = 0;
const planner = { identity: { model: 'controlled-browser-fixture' }, async next(context) {
  turn++;
  if (turn === 1) return { tool: 'observe', input: { pageId: 'main' } };
  if (turn === 2) {
    const observed = context.history.findLast(event => event.event === 'tool-result').output;
    return { tool: 'act', input: { kind: 'submit', target: { handle: observed.elements.find(element => element.selector === '#send').handle },
      effect: { external: true, effectKey: 'checkout-once' }, completion: { completedWhen: [{ kind: 'element-present', selector: '#not-confirmed' }] } } };
  }
  await gate.promise;
  return { tool: 'finish', input: { summary: 'Done' } };
} };
let app, browser;
const receipts = [];
try {
  app = await openWorkspaceApp({ stateDir: directory, config, port: 0, headless: true, planner, ...selected.selection });
  browser = await chromium.launch({ ...playwrightLaunchOptions(selected.config.browser), headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
  await page.goto(app.loginUrl);
  await page.getByLabel('What are we trying to find out?').fill('Why can a checkout create duplicate orders?');
  await page.getByLabel('Starting page').fill(origin);
  await page.getByRole('button', { name: 'Start investigation' }).click();
  await page.locator('#workspace').waitFor({ state: 'visible' });
  await page.getByRole('button', { name: 'Keep evidence', exact: true }).click();
  await page.locator('.artifact').first().waitFor();
  await page.locator('#record-form').locator('..').locator('summary').click();
  await page.locator('#record-form [name=kind]').selectOption('assumption');
  await page.locator('#record-form [name=text]').fill('A submitted request is always acknowledged.');
  await page.locator('#record-form button').click();
  await page.waitForFunction(() => document.querySelectorAll('.artifact').length === 2);
  const id = await page.evaluate(() => localStorage.getItem('fawn-project'));
  const assumption = Object.values(app.controller.store.get(id).artifacts).find(artifact => artifact.kind === 'assumption');
  const finding = app.controller.record(id, { kind: 'finding', text: 'A retry is safe', dependsOn: [assumption.id] });
  await page.waitForFunction(() => document.querySelectorAll('.artifact').length === 3);
  const decision = app.controller.record(id, { kind: 'decision', text: 'Retry the request', dependsOn: [finding.id] });
  await page.waitForFunction(() => document.querySelectorAll('.artifact').length === 4);
  const card = page.locator(`#artifact-${assumption.id}`);
  await card.getByRole('button', { name: 'Correct', exact: true }).click();
  await card.locator('textarea').fill('The response can be lost after submission.');
  await card.getByRole('button', { name: 'Save correction' }).click();
  await page.locator(`#artifact-${finding.id}.needs-review`).waitFor();
  assert.equal(app.controller.store.get(id).artifacts[assumption.id].revision, 2);
  const decisionCard = page.locator(`#artifact-${decision.id}`);
  await decisionCard.getByRole('button', { name: 'Correct', exact: true }).click();
  await decisionCard.locator('textarea').fill('Retry the request after checking the earlier result.');
  await decisionCard.getByRole('button', { name: 'Save correction' }).click();
  await page.waitForFunction(({ id, decisionId }) => {
    const card = document.getElementById(`artifact-${decisionId}`);
    return card?.classList.contains('needs-review') && card.textContent.includes('after checking the earlier result');
  }, { id, decisionId: decision.id });
  assert.equal(app.controller.store.get(id).artifacts[decision.id].revision, 2);
  assert.equal(app.controller.store.get(id).artifacts[decision.id].status, 'needs-review',
    'Editing a decision in the product cannot approve its unreviewed premise');
  await page.screenshot({ path: join(directory, 'desktop.png'), fullPage: true });
  await page.setViewportSize({ width: 430, height: 930 });
  await page.screenshot({ path: join(directory, 'compact.png'), fullPage: true });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Compact UI must not scroll horizontally');
  await page.locator('#delegate-form [name=task]').fill('Submit once, then stop if confirmation is unavailable.');
  await page.locator('#delegate-form [name=origins]').fill(origin);
  await page.locator('#delegate-form [name=submit]').check();
  await page.getByRole('button', { name: 'Give control to agent' }).click();
  await page.waitForFunction(() => document.querySelector('#run-status').textContent.includes('needs attention'), null, { timeout: 25000 });
  assert.equal(submissions, 1);
  assert.equal(app.controller.store.get(id).run.status, 'needs-attention');
  await assert.rejects(app.controller.delegate(id, { pageIds: ['main'], origins: [origin], actionKinds: ['submit'], task: 'Do it again' }), /unresolved/);
  await page.getByRole('button', { name: 'Check result', exact: true }).click();
  await page.waitForFunction(() => document.querySelector('#owner').textContent === 'You have control');
  assert.equal(submissions, 1, 'Check result must not resubmit');
  await page.screenshot({ path: join(directory, 'uncertainty.png'), fullPage: true });
  receipts.push({ check: 'human correction invalidates conclusions; unknown submission remains single and can be checked', passed: true });
  await browser.close(); browser = null;
  await app.close(); app = null;
  app = await openWorkspaceApp({ stateDir: directory, config, port: 0, headless: true, planner, ...selected.selection });
  const restored = await app.controller.status(id);
  assert.equal(restored.selected.workspace.ownerId, 'human');
  assert.ok(restored.selected.workspace.actions.some(action => action.isUncertain));
  assert.equal(submissions, 1);
  assert.ok(restored.selected.workspace.pages.some(value => value.needsReopen));
  const report = { classification: 'controlled-planner browser development evidence; no live-model or product-advantage claim', directory,
    receipts, submissions, modelCallsAfterRestart: turn - 2, viewportWidths: [1280, 430] };
  writeFileSync(join(directory, 'report.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
} finally { gate.resolve(); if (browser) await browser.close(); if (app) await app.close(); await new Promise(resolve => fixture.close(resolve)); }
