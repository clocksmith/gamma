// Real browser UI + real workspace service exercising personal workflow learn, reuse and repair.
// Synthetic application fixture and controlled planner only; no live-model or live-ATS claim.
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { chromium } from 'playwright-core';
import { openWorkspaceApp } from '../../src/client/main.js';
import { playwrightLaunchOptions } from '../../src/browser-launch.js';
import { sha256Hex } from '../../src/journal.js';
import { applicationFixture } from '../support/application-fixture.js';
import { testBrowserSelection } from '../support/browser-selection.js';
import { waitForProfileRelease } from '../../qualification/identity.js';

const directory = mkdtempSync(join(tmpdir(), 'fawn-product-workflow-ui-'));
const selected = testBrowserSelection(directory);
const config = { ...JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url))), pollMs: 200 };
const fixture = await applicationFixture();
const fields = [
  { slot: 'fullName', kind: 'fill', locator: ['textbox', 'Full name', 'input', 'text'] },
  { slot: 'email', kind: 'fill', locator: ['textbox', 'Email address', 'input', 'email'] },
  { slot: 'location', kind: 'fill', locator: ['textbox', 'Current city', 'input', 'text'] },
  { slot: 'workMode', kind: 'select', locator: ['combobox', 'Work arrangement', 'select', ''] },
  { slot: 'phone', kind: 'fill', locator: ['textbox', 'Phone number', 'input', 'tel'] },
];
const planner = { identity: { model: 'controlled-ui-workflow' }, next: async context => {
  for (const field of fields) {
    const element = context.observation.elements.find(value => value.label === field.locator[1]);
    if (element && element.value !== context.inputs[field.slot]) {
      return { tool: 'act', input: { kind: field.kind, handle: element.handle, slot: field.slot } };
    }
  }
  const button = context.observation.elements.find(value => value.tag === 'button'
    && ['Continue', 'Review application'].includes(value.label));
  return button ? { tool: 'act', input: { kind: 'click', handle: button.handle } }
    : { tool: 'finish', input: { summary: 'Review reached' } };
} };

let activeChanged = false;
const workflowPersistence = {
  ownerScope: 'ui-workflow-owner',
  limits: { maxNodes: 64, maxEdges: 64, maxSteps: 12 },
  maxBytes: 200000,
  lockWaitMs: 1000,
  lockRetryMs: 10,
};
const workflowTasks = new Map([['synthetic-application-v1', {
  label: 'Engineer application draft',
  accountScope: 'account-ui',
  task: 'Complete requested fields and stop at review without submitting.',
  planner,
  slotOptions: { workMode: ['Remote', 'Hybrid', 'Office'] },
  fieldGroups: [{ id: 'contact', steps: [
    ...fields.slice(0, 2).map(({ slot, kind, locator }) => ({ slot, kind, locators: [locator] })),
    { kind: 'click', locators: [['button', 'Continue', 'button', '']] },
  ] }, { id: 'questions', steps: [
    ...fields.slice(2, 4).map(({ slot, kind, locator }) => ({ slot, kind, locators: [locator] })),
    { kind: 'click', locators: [['button', 'Review application', 'button', '']] },
  ] }],
  disclosurePolicy: {
    origin: fixture.origin,
    fields,
    intermediateClicks: [['button', 'Continue', 'button', ''], ['button', 'Review application', 'button', '']],
  },
  verificationId: 'synthetic-ui-review-v1',
  taskSourceHashes: {
    self: sha256Hex(readFileSync(new URL(import.meta.url))),
    fixture: sha256Hex(readFileSync(new URL('../support/application-fixture.js', import.meta.url))),
  },
  verifyAccount: async ({ owner, pageId }) => {
    const state = await app.service.inspect(app.controller.admin(owner.workspaceId));
    const url = state.pages.find(page => page.pageId === pageId)?.url ?? '';
    return url.startsWith(`${fixture.origin}/application/`) ? 'account-ui' : 'unexpected';
  },
  verifyReview: async ({ service, owner, pageId, inputs }) => {
    const obs = await service.observe({ ...owner, pageId });
    const required = fields.filter(field => field.slot !== 'phone' || activeChanged);
    const completed = obs.text.includes('Review application')
      && required.every(field => obs.text.includes(field.locator[1]) && obs.text.includes(inputs[field.slot]));
    return { completed };
  },
}]]);

let app, browser;
try {
  const firstUrl = fixture.add('learn', false, 'Alpha', 'account-ui');
  const secondUrl = fixture.add('reuse', false, 'Beta', 'account-ui');
  const changedUrl = fixture.add('repair', true, 'Gamma', 'account-ui');
  const repeatedUrl = fixture.add('repeated', true, 'Delta', 'account-ui');

  app = await openWorkspaceApp({ stateDir: directory, config, port: 0, headless: true, planner,
    workflowPersistence, workflowTasks, ...selected.selection });
  browser = await chromium.launch({ ...playwrightLaunchOptions(selected.config.browser), headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
  await page.goto(app.loginUrl);
  await page.getByLabel('What are we trying to find out?').fill('Verify personal workflow delegation from UI');
  await page.getByLabel('Starting page').fill(firstUrl);
  await page.getByRole('button', { name: 'Start investigation' }).click();
  await page.locator('#workflow-panel').waitFor({ state: 'visible' });
  const waitForPageUrl = url => page.waitForFunction(expected => document.querySelector('#pages')?.textContent.includes(expected), url, { timeout: 15000 });
  await waitForPageUrl(firstUrl);

  await page.setViewportSize({ width: 430, height: 930 });
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    'Compact UI with personal workflow panel must not scroll horizontally');
  await page.setViewportSize({ width: 1280, height: 1000 });

  assert.equal(await page.locator('#workflow-mode').inputValue(), 'learn');
  assert.equal(await page.locator('#workflow-status').textContent(), 'Not learned yet');

  const fillInputs = async values => {
    for (const [slot, value] of Object.entries(values)) {
      const control = page.locator(`#workflow-fields [data-slot="${slot}"]`);
      const tag = await control.evaluate(el => el.tagName);
      if (tag === 'SELECT') await control.selectOption(value);
      else await control.fill(value);
    }
  };
  let projectId;
  try {
    projectId = await page.evaluate(() => localStorage.getItem('fawn-project'));
  const finishedCount = () => app.controller.store.get(projectId).activity
    .filter(entry => entry.event === 'personal-workflow-finished').length;

  await fillInputs({ fullName: 'Avery Test', email: 'avery@example.test', location: 'Albany', workMode: 'Remote', phone: '555-0100' });
  await page.locator('#run-workflow').click();
  await page.waitForFunction(() => document.querySelector('#workflow-status')?.textContent === 'Learned · rev 1', null, { timeout: 25000 });
  assert.equal(await page.locator('#workflow-mode').inputValue(), 'reuse', 'UI switches default mode to reuse once learned');
  assert.equal(finishedCount(), 1);
  const learnEvent = app.controller.store.get(projectId).activity.findLast(entry => entry.event === 'personal-workflow-finished');
  assert.equal(learnEvent.completed, true);
  assert.equal(learnEvent.modelCalls, 7);
  assert.equal(learnEvent.cacheSteps, 0);

  await page.locator('#navigate-form [name=url]').fill(secondUrl);
  await page.locator('#navigate-form button').click();
  await waitForPageUrl(secondUrl);
  await fillInputs({ fullName: 'Blair Example', email: 'blair@example.test', location: 'Boston', workMode: 'Hybrid', phone: '555-0101' });
  await page.locator('#run-workflow').click();
  await page.waitForFunction(() => document.querySelector('#activity')?.textContent.includes('6 cached, 0 model call(s)'), null, { timeout: 25000 });
  assert.equal(finishedCount(), 2);
  const reuseEvent = app.controller.store.get(projectId).activity.findLast(entry => entry.event === 'personal-workflow-finished');
  assert.equal(reuseEvent.completed, true);
  assert.equal(reuseEvent.modelCalls, 0);
  assert.equal(reuseEvent.cacheSteps, 6);

  activeChanged = true;
  await page.locator('#navigate-form [name=url]').fill(changedUrl);
  await page.locator('#navigate-form button').click();
  await waitForPageUrl(changedUrl);
  await page.locator('#run-workflow').click();
  await page.waitForFunction(() => document.querySelector('#workflow-status')?.textContent === 'Learned · rev 2', null, { timeout: 25000 });
  assert.equal(finishedCount(), 3);
  const repairEvent = app.controller.store.get(projectId).activity.findLast(entry => entry.event === 'personal-workflow-finished');
  assert.equal(repairEvent.completed, true);
  assert.equal(repairEvent.cacheSteps, 5);
  assert.equal(repairEvent.modelCalls, 3);

  await page.locator('#navigate-form [name=url]').fill(repeatedUrl);
  await page.locator('#navigate-form button').click();
  await waitForPageUrl(repeatedUrl);
  await fillInputs({ fullName: 'Casey Sample', email: 'casey@example.test', location: 'Chicago', workMode: 'Office', phone: '555-0102' });
  await page.locator('#run-workflow').click();
  await page.waitForFunction(() => document.querySelector('#activity')?.textContent.includes('7 cached, 0 model call(s)'), null, { timeout: 25000 });
  assert.equal(finishedCount(), 4);
  const repeatedEvent = app.controller.store.get(projectId).activity.findLast(entry => entry.event === 'personal-workflow-finished');
  assert.equal(repeatedEvent.completed, true);
  assert.equal(repeatedEvent.cacheSteps, 7);
  assert.equal(repeatedEvent.modelCalls, 0);

  const stored = JSON.parse(readFileSync(join(directory, 'workflows/workflows.private.json'), 'utf8'));
  const secretKey = Object.values(stored.workflowVersions)[0].dag.key;
  const rawStatus = await page.evaluate(async id => (await fetch(`/api/status?project=${encodeURIComponent(id)}`)).text(), projectId);
  assert.ok(!rawStatus.includes(secretKey), 'Browser status API must not expose workflow HMAC key');
  assert.ok(!rawStatus.includes('adminCredential'));
  console.log('ok: UI personal workflow learn -> 0-call reuse -> changed-form repair -> 0-call repaired reuse, compact viewport and secret containment');
  } catch (error) {
    if (projectId && app) console.error('UI workflow debug:', JSON.stringify(app.controller.store.get(projectId), null, 2));
    throw error;
  }
} finally {
  if (browser) await browser.close();
  if (app) await app.close();
  await fixture.close();
  await waitForProfileRelease(directory);
  rmSync(directory, { recursive: true, force: true });
}
