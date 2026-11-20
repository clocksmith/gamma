// Fawn workspace comparison — competent stock Chromium/Playwright baseline.
//
// The same three tasks without the workspace service, written as careful automation would be:
// a persistent profile, a durable progress file, an origin allowlist that also covers form
// actions, exact accessible-name locators resolved at action time, the application's supported
// idempotency reference, and an application-state check before resubmitting after interruption.

import { createHash } from 'node:crypto';
import { closeSync, existsSync, fsyncSync, mkdirSync, openSync, readFileSync, renameSync, writeSync } from 'node:fs';
import { join } from 'node:path';

const PASSAGE_SEPARATOR = /\n+/;
const UNSAFE_FILENAME_CHARS = /[^A-Za-z0-9._-]/g;

class OriginNotAllowed extends Error {
  constructor(url) {
    super(`origin of ${url} is not allowed`);
    this.code = 'origin-not-allowed';
  }
}

/** Durable task progress: rewritten atomically and fsynced before the next step. */
class ProgressFile {
  constructor(path) {
    this._path = path;
    this._entries = existsSync(path) ? JSON.parse(readFileSync(path, 'utf8')) : {};
  }

  get(key) {
    return this._entries[key] ?? null;
  }

  set(key, value) {
    this._entries[key] = value;
    const temporary = `${this._path}.tmp`;
    const fd = openSync(temporary, 'w');
    writeSync(fd, JSON.stringify(this._entries));
    fsyncSync(fd);
    closeSync(fd);
    renameSync(temporary, this._path);
  }
}

function taskKey(formUrl, fields) {
  const sorted = Object.fromEntries(Object.entries(fields).sort(([a], [b]) => (a < b ? -1 : 1)));
  return createHash('sha256').update(JSON.stringify({ formUrl, fields: sorted })).digest('hex');
}

function requireAllowed(env, url) {
  let origin = null;
  try {
    origin = new URL(url).origin;
  } catch {
    throw new OriginNotAllowed(url);
  }
  if (!env.allowedOrigins.includes(origin)) throw new OriginNotAllowed(url);
}

function isAllowed(env, url) {
  try {
    requireAllowed(env, url);
    return true;
  } catch {
    return false;
  }
}

async function runResearch(env, task) {
  const { page, read } = env;
  requireAllowed(env, task.indexUrl);
  await page.goto(task.indexUrl, { waitUntil: 'load' });
  const links = await read(() => page.locator('a[href]').evaluateAll((nodes) => nodes.map((node) => ({
    href: node.href,
    text: node.textContent.trim(),
  }))));
  const topics = task.topics.map((topic) => topic.toLowerCase());
  const documents = links.filter((link) => topics.some((topic) => link.text.toLowerCase().includes(topic))).slice(0, task.maxDocuments);
  const findings = [];
  const skipped = [];
  for (const document of documents) {
    if (!isAllowed(env, document.href)) {
      skipped.push(document.href);
      continue;
    }
    await page.goto(document.href, { waitUntil: 'load' });
    const content = await read(() => page.evaluate(() => ({ title: window.document.title, text: window.document.body.innerText })));
    const passages = content.text.split(PASSAGE_SEPARATOR).filter((passage) => topics.some((topic) => passage.toLowerCase().includes(topic)));
    findings.push({ url: page.url(), title: content.title, passages });
  }
  return { status: 'completed', findings, skipped };
}

async function runForm(env, task) {
  const { page, read, progress } = env;
  const key = taskKey(task.formUrl, task.fields);
  const previous = progress.get(key);
  if (previous?.state === 'confirmed') return { status: 'completed', recovered: 'progress-file' };
  if (previous?.state === 'failed') return { status: 'failed', recovered: 'progress-file' };
  if (previous?.state === 'submitting' && !task.fields.reference) {
    // Interrupted after the click: the application's own list decides before any resubmission.
    requireAllowed(env, task.submissionsUrl);
    await page.goto(task.submissionsUrl, { waitUntil: 'load' });
    const listing = await read(() => page.locator(task.submissionsSelector).innerText());
    if (listing.includes(`${task.fields.name} ${task.fields.email}`)) {
      progress.set(key, { state: 'confirmed', basis: 'application-state' });
      return { status: 'completed', recovered: 'application-state' };
    }
  }
  requireAllowed(env, task.formUrl);
  await page.goto(task.formUrl, { waitUntil: 'load' });
  for (const [name, value] of Object.entries(task.fields)) await page.locator(`[name="${name}"]`).fill(value);
  const action = await read(() => page.locator('form').evaluate((form) => form.action));
  requireAllowed(env, action);
  const submit = page.getByRole('button', { name: task.submitName, exact: true });
  await read(() => submit.textContent());
  await env.beforeEffect();
  progress.set(key, { state: 'submitting' });
  await submit.click();
  await page.locator(`${task.completedSelector}, ${task.failedSelector}`).first().waitFor();
  const confirmed = await page.locator(task.completedSelector).count() > 0;
  progress.set(key, { state: confirmed ? 'confirmed' : 'failed' });
  return { status: confirmed ? 'completed' : 'failed' };
}

async function runExport(env, task) {
  const { page, read } = env;
  requireAllowed(env, task.exportUrl);
  await page.goto(task.exportUrl, { waitUntil: 'load' });
  const link = page.getByRole('link', { name: task.linkText, exact: true });
  const href = await read(() => link.getAttribute('href'));
  requireAllowed(env, new URL(href, page.url()).href);
  await env.beforeEffect();
  const [download] = await Promise.all([page.waitForEvent('download'), link.click()]);
  mkdirSync(env.artifactDir, { recursive: true });
  const artifactPath = join(env.artifactDir, `${task.runId.replace(UNSAFE_FILENAME_CHARS, '_')}-${download.suggestedFilename()}`);
  await download.saveAs(artifactPath);
  const bytes = readFileSync(artifactPath);
  return { status: 'completed', artifact: { artifactPath, sha256: createHash('sha256').update(bytes).digest('hex') } };
}

const BASELINE_WORKFLOWS = Object.freeze({ research: runResearch, form: runForm, export: runExport });

export { BASELINE_WORKFLOWS, ProgressFile };
