// Real browser UI + real workspace service. A person keeps repository sources, records a finding and
// competing explanations, then the file changes: the workspace says what changed, which records need
// rechecking and what still holds, and the person corrects them, all through the product UI.
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { chromium } from 'playwright-core';
import { openWorkspaceApp } from '../../src/client/main.js';
import { playwrightLaunchOptions } from '../../src/browser-launch.js';
import { testBrowserSelection } from '../support/browser-selection.js';

const directory = mkdtempSync(join(tmpdir(), 'fawn-memory-ui-')), repository = join(directory, 'repository');
mkdirSync(join(repository, 'src'), { recursive: true });
writeFileSync(join(repository, 'src/cache.js'), 'export const TTL_SECONDS = 300;\n');
writeFileSync(join(repository, 'src/retry.js'), 'export const MAX_ATTEMPTS = 3;\n');
const selected = testBrowserSelection(directory);
const config = JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url)));
let app, browser;
try {
  app = await openWorkspaceApp({ stateDir: join(directory, 'state'), config, port: 0, headless: true, planner: null, ...selected.selection });
  browser = await chromium.launch({ ...playwrightLaunchOptions(selected.config.browser), headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 1100 } });
  await page.goto(app.loginUrl);
  await page.getByLabel('What are we trying to find out?').fill('Why do prices go stale?');
  await page.locator('#create-form [name=repositoryRoot]').evaluate((input, value) => { input.closest('details')?.setAttribute('open', ''); input.value = value; }, repository);
  await page.getByRole('button', { name: 'Start investigation' }).click();
  await page.locator('#workspace').waitFor({ state: 'visible' });
  const id = await page.evaluate(() => localStorage.getItem('fawn-project'));
  const artifacts = () => Object.values(app.controller.store.get(id).artifacts);
  const count = number => page.waitForFunction(expected => document.querySelectorAll('.artifact').length === expected, number);

  // Keep two repository sources through the UI.
  await page.locator('#repository-form').locator('..').locator('summary').click();
  for (const [index, path] of ['src/cache.js', 'src/retry.js'].entries()) {
    await page.locator('#repository-form [name=path]').fill(path);
    await page.locator('#repository-form button').click();
    await count(index + 1);
  }
  const cache = artifacts().find(value => value.source?.path === 'src/cache.js'), retry = artifacts().find(value => value.source?.path === 'src/retry.js');
  // A finding on one source, a second on the other, and a competing explanation that is rejected.
  const record = async (kind, text, dependsOn, expected) => {
    if (!await page.locator('#record-form').isVisible()) await page.locator('#record-form').locator('..').locator('summary').click();
    await page.locator('#record-form [name=kind]').selectOption(kind);
    await page.locator('#record-form [name=text]').fill(text);
    for (const key of dependsOn) await page.locator(`#record-form input[name=dependsOn][value="${key}"]`).check();
    await page.locator('#record-form button').click();
    await count(expected);
    return artifacts().find(value => value.text === text);
  };
  const finding = await record('finding', 'Prices are cached for five minutes.', [cache.id], 3);
  const other = await record('finding', 'Failed fetches are retried three times.', [retry.id], 4);
  const hypothesis = await record('hypothesis', 'Retries replay an old response.', [retry.id], 5);
  assert.deepEqual(hypothesis.disposition, { state: 'open', reason: '' });
  const card = page.locator(`#artifact-${hypothesis.id}`);
  await card.getByRole('button', { name: 'Reject', exact: true }).click();
  await card.locator('textarea').fill('retry.js only repeats the request.');
  await card.getByRole('button', { name: 'Save as rejected' }).click();
  await card.getByText('Rejected: retry.js only repeats the request.').waitFor();
  assert.equal(app.controller.store.get(id).artifacts[hypothesis.id].disposition.state, 'rejected');

  // The file changes. One click says what that means.
  writeFileSync(join(repository, 'src/cache.js'), 'export const TTL_SECONDS = 900;\n');
  await page.getByRole('button', { name: 'Check saved sources for changes' }).click();
  const validity = page.locator('#validity');
  await validity.getByText('src/cache.js changed from line 1 (1 removed, 1 added); 1 record(s) rest on it.').waitFor();
  await validity.getByText('1 record(s) need rechecking, 1 still hold, 1 rejected explanation(s) kept.').waitFor();
  await validity.getByText(/Next: Recheck 1 record\(s\) against the changed sources/).waitFor();
  await page.locator(`#artifact-${finding.id}.needs-review`).waitFor();
  assert.equal(await page.locator(`#artifact-${other.id}.needs-review`).count(), 0, 'the finding on the unchanged file is left alone');

  // The person corrects the finding; nothing is left to recheck.
  const stale = page.locator(`#artifact-${finding.id}`);
  await stale.getByRole('button', { name: 'Correct', exact: true }).click();
  await stale.locator('textarea').fill('Prices are cached for fifteen minutes.');
  await stale.getByRole('button', { name: 'Save correction' }).click();
  await page.locator(`#artifact-${finding.id}.current`).waitFor();
  await validity.getByText('0 record(s) need rechecking, 2 still hold, 1 rejected explanation(s) kept.').waitFor();
  assert.equal(app.controller.store.get(id).artifacts[finding.id].text, 'Prices are cached for fifteen minutes.');
  console.log('ok: UI keeps repository sources, settles a competing explanation with a reason, reports a changed file with the records resting on it, and clears after the person corrects them');
} finally {
  await browser?.close().catch(() => {}); await app?.close().catch(() => {});
  rmSync(directory, { recursive: true, force: true });
}
