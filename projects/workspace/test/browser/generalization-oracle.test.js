// Deliberately write a wrong field to prove the independent oracle rejects retained values.
import assert from 'node:assert/strict';
import { chromium } from 'playwright-core';
import { createFixture } from '../../qualification/workflow-generalization/fixture.js';

const fixture = await createFixture();
const browser = await chromium.launch({ channel: process.env.FAWN_WORKSPACE_TEST_BROWSER_CHANNEL ?? 'chrome', headless: true });
try {
  const page = await browser.newPage(), postResponses = [];
  page.on('response', response => {
    if (response.request().method() !== 'GET') postResponses.push(response.url());
  });
  await page.goto(fixture.add('oracle', 'lever', 'evaluate', 'semantic-decoy'));
  const email = 'semantic-check@example.test';
  await page.locator('#email-decoy').fill(email);
  assert.equal(await page.locator('#email-decoy').inputValue(), email, 'Read-back alone passes');
  const rejected = await fixture.verify('oracle', page, { email });
  assert.equal(rejected.completed, false);
  assert.equal(rejected.wrongFieldFills, 1);
  assert.equal(rejected.wrongWrites[0].id, 'email-decoy');
  const connection = await page.evaluate(async () => {
    try { await fetch('https://example.test/no-disclosure', { method: 'POST', body: 'sentinel' }); return 'unexpected'; }
    catch { return 'blocked'; }
  });
  assert.equal(connection, 'blocked');
  assert.deepEqual(postResponses, []);
  // Chromium can report a blocked fetch as a request event: no response or network transmission
  // follows. The CSP result is the assertion; request count is not a disclosure oracle.
  assert.equal(await page.locator('form').count(), 0);
  console.log('ok: retained wrong-field write fails semantic oracle; local projection forbids network and final submission');
} finally { await browser.close(); await fixture.close(); }
