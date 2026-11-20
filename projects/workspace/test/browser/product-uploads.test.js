// Actual loopback UI, local file choice and controlled planner. No real document or live site.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { chromium } from 'playwright-core';
import { openWorkspaceApp } from '../../src/client/main.js';
import { playwrightLaunchOptions } from '../../src/browser-launch.js';
import { testBrowserSelection } from '../support/browser-selection.js';
import { sha256Hex } from '../../src/journal.js';

const bytes = Buffer.from('A harmless file selected in the local control UI.\n');
const received = [];
const fixture = createServer(async (req, res) => {
  if (req.method === 'POST') {
    const chunks = []; for await (const chunk of req) chunks.push(chunk);
    received.push(sha256Hex(Buffer.concat(chunks))); res.end('accepted'); return;
  }
  res.setHeader('content-type', 'text/html');
  res.end(`<title>Local attachment fixture</title><label for="file">Attachment</label><input id="file" type="file" hidden><p id="receipt"></p><script>
    document.querySelector('#file').onchange = async event => {
      await fetch('/accept', { method: 'POST', body: await event.target.files[0].arrayBuffer() });
      document.querySelector('#receipt').textContent = 'Attachment accepted';
    };</script>`);
});
await new Promise(resolve => fixture.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${fixture.address().port}`;
const directory = mkdtempSync(join(tmpdir(), 'fawn-product-uploads-'));
const selected = testBrowserSelection(directory);
const base = JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url)));
let turns = 0;
const planner = { identity: { model: 'controlled-upload-fixture' }, async next(context) {
  turns++;
  assert.ok(!JSON.stringify(context).includes(bytes.toString('base64')), 'Planner gets descriptors, never local file bytes');
  if (turns === 1) return { tool: 'observe', input: { pageId: 'main' } };
  if (turns === 2) {
    const observed = context.history.findLast(event => event.event === 'tool-result').output;
    const file = context.permissions.uploadFiles[0];
    return { tool: 'act', input: { pageId: 'main', kind: 'upload',
      target: { handle: observed.elements.find(element => element.selector === '#file').handle },
      params: { fileIds: [file.fileId] }, effect: { external: true, effectKey: 'one-local-attachment' },
      completion: { completedWhen: [{ kind: 'element-text-includes', selector: '#receipt', value: 'Attachment accepted' }] } } };
  }
  return { tool: 'finish', input: { summary: 'Local attachment accepted' } };
} };
let app, browser;
try {
  app = await openWorkspaceApp({ stateDir: directory, config: { ...base, pollMs: 50 }, port: 0, headless: true, planner, ...selected.selection });
  browser = await chromium.launch({ ...playwrightLaunchOptions(selected.config.browser), headless: true });
  const page = await browser.newPage({ viewport: { width: 430, height: 930 } });
  await page.goto(app.loginUrl);
  await page.getByLabel('What are we trying to find out?').fill('Attach this explicitly selected local fixture');
  await page.getByLabel('Starting page').fill(origin);
  await page.getByRole('button', { name: 'Start investigation' }).click();
  await page.locator('#workspace').waitFor({ state: 'visible' });
  await page.locator('#delegate-form [name=task]').fill('Attach the authorized file, verify the receipt, then stop. Do not submit a form.');
  await page.locator('#delegate-form [name=origins]').fill(origin);
  await page.locator('#delegate-form [name=uploadFiles]').setInputFiles({ name: 'local.txt', mimeType: 'text/plain', buffer: bytes });
  let confirmations = 0;
  page.on('dialog', dialog => {
    assert.ok(dialog.message().includes('local.txt') && dialog.message().includes(origin));
    confirmations++;
    return confirmations === 1 ? dialog.dismiss() : dialog.accept();
  });
  const delegate = page.getByRole('button', { name: 'Give control to agent' });
  await delegate.click();
  assert.equal(turns, 0, 'Cancelling disclosure confirmation must not call the planner');
  await delegate.click();
  await page.waitForFunction(() => document.querySelector('#owner').textContent === 'You have control'
    && document.querySelector('#run-status').textContent.toLowerCase().includes('completed'));
  assert.deepEqual(received, [sha256Hex(bytes)]);
  assert.equal(confirmations, 2);
  assert.equal(await page.locator('[name=uploadFiles]').inputValue(), '', 'File selection does not carry over into a later task');
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  const id = await page.evaluate(() => localStorage.getItem('fawn-project'));
  const state = await app.service.inspect(app.controller.admin(id));
  assert.ok(state.actions.some(action => action.kind === 'upload' && action.outcome === 'completed'));
  assert.equal(state.grants.filter(grant => grant.ownerId === 'agent').length, 0);
  console.log('ok: local UI file selection, cancelled/approved disclosure, descriptor-only planner, exact attachment, revoked delegation and phone layout');
} finally {
  await browser?.close(); await app?.close();
  await new Promise(resolve => fixture.close(resolve));
  rmSync(directory, { recursive: true, force: true });
}
