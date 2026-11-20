// Automated instrument check only. These actions must never count as a human participant run.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:net';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { once } from 'node:events';
import { chromium } from 'playwright-core';

const root = mkdtempSync(join(tmpdir(), 'fawn-participant-instrument-'));
const probe = createServer();
await new Promise(resolve => probe.listen(0, '127.0.0.1', resolve));
const port = probe.address().port;
await new Promise(resolve => probe.close(resolve));
const directory = join(root, 'run');
const script = fileURLToPath(new URL('../../qualification/workflow-generalization/participant.js', import.meta.url));
const child = spawn(process.execPath, [script, '--out', directory, '--port', String(port)], { stdio: ['ignore', 'pipe', 'pipe'] });
child.stderr.resume();
let browser;
try {
  const ready = await new Promise((resolve, reject) => {
    let text = '';
    const timeout = setTimeout(() => reject(Error('Participant startup deadline')), 30000);
    child.once('error', reject);
    child.once('exit', code => { clearTimeout(timeout); reject(Error(`Participant exited: ${code}`)); });
    child.stdout.on('data', bytes => {
      text += bytes;
      if (text.includes('\n')) { clearTimeout(timeout); resolve(JSON.parse(text.split('\n')[0])); }
    });
  });
  const url = new URL(ready.participantUrl), origin = url.origin;
  const headers = { authorization: `Bearer ${url.hash.slice(1)}` };
  browser = await chromium.launch({ channel: 'chrome', headless: true });
  const ui = await browser.newPage({ viewport: { width: 1080, height: 900 } });
  await ui.goto(ready.participantUrl);
  await ui.getByRole('button', { name: 'Start next task', exact: true }).waitFor();
  assert.equal((await fetch(origin + '/status')).status, 403);
  const markup = await (await fetch(origin)).text();
  assert.ok(markup.includes('Teach, reuse, repair, repeat'));
  assert.equal((await fetch(origin + '/command', { method: 'POST', headers: { ...headers, origin: 'http://other.invalid' }, body: '{"operation":"start"}' })).status, 403);
  const status = async () => (await fetch(origin + '/status', { headers })).json();
  const command = async input => {
    const response = await fetch(origin + '/command', { method: 'POST', headers: { ...headers, origin, 'content-type': 'application/json' }, body: JSON.stringify(input) });
    const result = await response.json();
    return { response, result };
  };
  await command({ operation: 'start' });
  await ui.getByText('First Name', { exact: true }).waitFor();
  const selection = ui.locator('article').filter({ has: ui.getByText('First Name', { exact: true }) }).locator('select');
  await selection.selectOption('firstName');
  await ui.waitForTimeout(1700);
  assert.equal(await selection.inputValue(), 'firstName', 'Status polling must not erase a participant choice');
  await ui.reload();
  await ui.getByText('First Name', { exact: true }).waitFor();
  if (process.env.FAWN_PARTICIPANT_SCREENSHOT) await ui.screenshot({ path: process.env.FAWN_PARTICIPANT_SCREENSHOT, fullPage: true });
  const before = await status();
  const wrong = await command({ operation: 'act', handle: before.current.observation.elements[0].handle, slot: 'email' });
  assert.equal(wrong.response.status, 400);
  assert.equal((await status()).stopped, true);
  assert.equal((await command({ operation: 'restart' })).response.status, 200);
  const slots = { 'First Name': 'firstName', 'Last Name': 'lastName', Email: 'email', Phone: 'phone',
    'Work arrangement': 'workMode', 'Current city': 'city' };
  for (let task = 0; task < 4; task++) {
    assert.equal((await command({ operation: 'start' })).response.status, 200);
    for (let turn = 0; turn < 12; turn++) {
      const state = await status();
      if (state.current.record.verification.completed) break;
      const elements = state.current.observation.elements;
      const field = elements.find(element => slots[element.label] && element.value !== state.inputs[slots[element.label]]);
      const target = field ?? elements.find(element => ['Continue', 'Review application'].includes(element.label));
      assert.ok(target);
      const action = await command({ operation: 'act', handle: target.handle, ...(field ? { slot: slots[field.label] } : {}) });
      assert.equal(action.response.status, 200, action.result.error);
    }
    assert.equal((await command({ operation: 'confirm' })).response.status, 200);
  }
  const receipt = JSON.parse(readFileSync(join(directory, 'participant.json')));
  assert.equal(receipt.completed, true);
  assert.equal(receipt.sourceUnchanged, true);
  assert.ok(receipt.records[0].abandonedAt);
  const confirmed = receipt.records.filter(record => record.confirmedAt);
  assert.deepEqual(confirmed.map(record => record.cachedSteps), [0, 7, 4, 4]);
  assert.deepEqual(confirmed.map(record => record.humanActions), [7, 0, 4, 4]);
  assert.deepEqual(confirmed.map(record => record.repairRequests), [0, 0, 1, 1]);
  assert.ok(confirmed.every(record => record.verification.wrongFieldFills === 0 && record.verification.submissions === 0));
  assert.equal(receipt.productAdvantageEstablished, false);
  console.log('ok: participant instrument teaches/reuses, preserves failed attempts and exposes repeated repair; not a user result');
} finally {
  await browser?.close();
  const exited = once(child, 'exit'); child.kill('SIGTERM'); await exited;
  rmSync(root, { recursive: true, force: true });
}
