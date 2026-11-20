import { CHROMIUM_SURFACE_V1 } from '../surface-contract.js';
import { pickRegion } from './region-picker.js';
// Fawn workspace — narrow Playwright adapter over stock Chromium
//
// Only the service constructs this adapter. Chromium is launched over Playwright's private pipe
// with a persistent per-workspace profile, so no debugging endpoint exists for other clients.

import { createHash, randomUUID } from 'node:crypto';
import { mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { chromium } from 'playwright-core';
import { buildProbe, buildSnapshot, elementArgs, queryPage, snapshotArgs } from './page-query.js';
import { performChoice } from './choice-query.js';
import { playwrightLaunchOptions } from '../browser-launch.js';
import { closeWithin } from './bounded-close.js';

const UNSAFE_FILENAME_CHARS = /[^A-Za-z0-9._-]/g;

class PlaywrightWorkspaceAdapter {
  get surfaceVersion() { return CHROMIUM_SURFACE_V1; }

  constructor({ config, profileRoot, artifactRoot }) {
    this._config = config;
    this._profileRoot = profileRoot;
    this._artifactRoot = artifactRoot;
    this._workspaces = new Map();
  }

  async openWorkspace(workspaceId, { pages = [] } = {}) {
    if (this._workspaces.has(workspaceId)) return;
    const profileDir = join(this._profileRoot, workspaceId);
    const launchOptions = playwrightLaunchOptions(this._config.browser);
    mkdirSync(profileDir, { recursive: true });
    const context = await chromium.launchPersistentContext(profileDir, {
      ...launchOptions,
      headless: this._config.browser.headless,
      acceptDownloads: true,
      timeout: this._config.dispatch.actionTimeoutMs,
    });
    try {
      const page = context.pages()[0] ?? await context.newPage();
      page.setDefaultTimeout(this._config.dispatch.actionTimeoutMs);
      const entry = { context, page, profileDir, pages: new Map([['main', page]]) };
      this._workspaces.set(workspaceId, entry);
      for (const saved of pages.filter(value => value.pageId !== 'main')) {
        const restored = await context.newPage();
        entry.pages.set(saved.pageId, restored);
      }
      context.on('page', next => {
        if (![...entry.pages.values()].includes(next)) entry.pages.set(`page-${randomUUID()}`, next);
        next.setDefaultTimeout(this._config.dispatch.actionTimeoutMs);
      });
    } catch (error) {
      this._workspaces.delete(workspaceId);
      await context.close();
      throw error;
    }
  }

  _page(workspaceId, pageId = 'main') {
    const entry = this._workspaces.get(workspaceId);
    if (!entry) throw new Error(`workspace ${workspaceId} has no open browser`);
    const page = entry.pages.get(pageId);
    if (!page || page.isClosed()) throw new Error(`Page ${pageId} is closed or unknown`);
    return page;
  }

  async snapshot(workspaceId, read = {}) {
    const raw = await this._page(workspaceId, read.pageId).evaluate(queryPage, snapshotArgs(this._config, read));
    return buildSnapshot(raw, this._workspaces.get(workspaceId).context.pages().length);
  }

  async probeUrl(workspaceId, pageId = 'main') {
    return this._page(workspaceId, pageId).url();
  }

  async probeElement(workspaceId, selector, pageId = 'main', readRoots = null) {
    return buildProbe(await this._page(workspaceId, pageId).evaluate(queryPage, { ...elementArgs(selector), readRoots }));
  }

  /**
   * Perform one admitted mutation. Called only by the service's dispatcher.
   */
  async execute(workspaceId, request, uploadFiles) {
    const page = this._page(workspaceId, request.pageId);
    const effect = EFFECTS[request.kind];
    if (!effect) throw new Error(`unsupported action kind ${request.kind}`);
    return effect.call(this, page, request, workspaceId, uploadFiles);
  }

  async listPages(workspaceId) {
    const { context, pages } = this._workspaces.get(workspaceId);
    for (const page of context.pages()) if (![...pages.values()].includes(page)) pages.set(`page-${randomUUID()}`, page);
    return Promise.all([...pages].map(async ([pageId, page]) => {
      const opener = await page.opener().catch(() => null);
      return { pageId, url: page.url(), title: page.isClosed() ? '' : await page.title().catch(() => ''),
        closed: page.isClosed(), openerId: [...pages].find(([, candidate]) => candidate === opener)?.[0] ?? null };
    }));
  }

  async openPage(workspaceId, pageId) {
    const entry = this._workspaces.get(workspaceId);
    const page = await entry.context.newPage();
    for (const [id, current] of entry.pages) if (current === page) entry.pages.delete(id);
    entry.pages.set(pageId, page);
  }

  async selectRegion(workspaceId, pageId) {
    const page = this._page(workspaceId, pageId);
    await page.bringToFront();
    return page.evaluate(pickRegion, this._config.dispatch.actionTimeoutMs);
  }

  async focusPage(workspaceId, pageId) { await this._page(workspaceId, pageId).bringToFront(); }

  /**
   * Resolves to { workspaceId, release, survivors?, errors? } per workspace (see bounded-close.js).
   * A workspace whose browser could not be shown to have exited stays owned by this adapter.
   */
  async close({ timeoutMs = this._config.dispatch.actionTimeoutMs, releaseBrowser = closeWithin } = {}) {
    // Releasing the workspace never waits on a browser that will not exit.
    return Promise.all([...this._workspaces.entries()].map(async ([workspaceId, entry]) => {
      const { release, survivors, errors } = await releaseBrowser(entry.context, { profileDir: entry.profileDir, timeoutMs });
      if (release !== 'unresolved' && this._workspaces.get(workspaceId) === entry) this._workspaces.delete(workspaceId);
      return { workspaceId, release, ...(survivors.length ? { survivors } : {}), ...(errors.length ? { errors } : {}) };
    }));
  }
}

const EFFECTS = Object.freeze({
  async upload(page, request, workspaceId, files) {
    if (!files?.length) throw new Error('Upload bytes must come from trusted dispatch');
    await page.locator(request.target.selector).setInputFiles(files.map(file => file.path));
    return { files: files.map(({ fileId, name, byteLength, sha256 }) => ({ fileId, name, byteLength, sha256 })) };
  },
  async navigate(page, request) {
    const response = await page.goto(request.target.url, { waitUntil: 'load' });
    return { status: response?.status() ?? null, finalUrl: page.url() };
  },
  async click(page, request) {
    await page.locator(request.target.selector).click();
    return { selector: request.target.selector };
  },
  async submit(page, request) {
    await page.locator(request.target.selector).click();
    return { selector: request.target.selector };
  },
  async fill(page, request) {
    await page.locator(request.target.selector).fill(request.params.value);
    return { selector: request.target.selector };
  },
  async select(page, request) {
    const { completionPollMs, completionTimeoutMs } = this._config.dispatch;
    return performChoice({
      evaluate: (fn, args) => page.evaluate(fn, args),
      clickSelector: (selector) => page.locator(selector).click(),
      clickPoint: (x, y) => page.mouse.click(x, y),
      setNative: (selector, value) => page.locator(selector).selectOption({ value }),
    }, { selector: request.target.selector, value: request.params.value, pollMs: completionPollMs, timeoutMs: completionTimeoutMs });
  },
  async download(page, request, workspaceId) {
    const directory = join(this._artifactRoot, workspaceId);
    mkdirSync(directory, { recursive: true });
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.locator(request.target.selector).click(),
    ]);
    const safeName = download.suggestedFilename().replace(UNSAFE_FILENAME_CHARS, '_');
    const artifactPath = join(directory, `${request.actionId.replace(UNSAFE_FILENAME_CHARS, '_')}-${safeName}`);
    await download.saveAs(artifactPath);
    const bytes = readFileSync(artifactPath);
    return {
      artifactPath,
      suggestedFilename: download.suggestedFilename(),
      byteLength: bytes.length,
      sha256: createHash('sha256').update(bytes).digest('hex'),
    };
  },
});

function createPlaywrightAdapter(options) {
  return new PlaywrightWorkspaceAdapter(options);
}

export { createPlaywrightAdapter };
