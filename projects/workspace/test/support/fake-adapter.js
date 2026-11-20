// Fawn workspace tests — in-memory page model with an on-disk external receipt log
//
// Exercises service semantics without a browser. External submissions append to a receipts
// file outside the service state directory so restart tests have an independent oracle.

import { appendFileSync, existsSync, readFileSync } from 'node:fs';
import { canonicalJson, sha256Hex } from '../../src/journal.js';

const BLANK_URL = 'about:blank';
const ORIGIN = 'https://fixture.test';
const FOREIGN_ORIGIN = 'https://foreign.test';

const SITE = Object.freeze({
  [`${ORIGIN}/form`]: {
    title: 'Contact form',
    text: 'Contact form',
    elements: [
      { selector: '#name', tag: 'input', attributes: [['id', 'name'], ['name', 'name']], text: '', isInput: true },
      { selector: '#email', tag: 'input', attributes: [['id', 'email'], ['name', 'email']], text: '', isInput: true },
      {
        selector: '#send',
        tag: 'button',
        attributes: [['id', 'send'], ['type', 'submit']],
        text: 'Send',
        formAction: `${ORIGIN}/form/submit`,
        submitsTo: `${ORIGIN}/form/done`,
      },
      { selector: '#other', tag: 'a', attributes: [['href', '/other'], ['id', 'other']], text: 'Other', navigatesTo: `${ORIGIN}/other` },
      {
        selector: '#elsewhere',
        tag: 'a',
        attributes: [['href', `${FOREIGN_ORIGIN}/`], ['id', 'elsewhere']],
        text: 'Elsewhere',
        navigatesTo: `${FOREIGN_ORIGIN}/`,
      },
    ],
    regions: { '#contact': ['#name', '#email', '#send'] },
  },
  [`${ORIGIN}/form/done`]: {
    title: 'Done',
    text: 'Submission received',
    elements: [{ selector: '#receipt', tag: 'p', attributes: [['id', 'receipt']], text: 'Submission received' }],
  },
  [`${ORIGIN}/other`]: {
    title: 'Other',
    text: 'Other page',
    elements: [{ selector: '#back', tag: 'a', attributes: [['href', '/form'], ['id', 'back']], text: 'Back', navigatesTo: `${ORIGIN}/form` }],
  },
  [`${ORIGIN}/export`]: {
    title: 'Export',
    text: 'Export',
    elements: [{
      selector: '#report',
      tag: 'a',
      attributes: [['href', '/report.csv'], ['id', 'report']],
      text: 'Report',
      href: `${ORIGIN}/report.csv`,
      downloads: 'a,b\n1,2\n',
    }],
  },
});

function digestOf(element) {
  return sha256Hex(canonicalJson({ tag: element.tag, attributes: element.attributes, text: element.text }));
}

function freshPage(url) {
  return { url, values: {}, mutation: 0, regionMutations: {}, textOverrides: {} };
}

class FakeAdapter {
  constructor({ receiptsPath }) {
    this.receiptsPath = receiptsPath;
    this.pages = new Map();
    this.held = null;
    this.nextFailure = null;
    this.executions = [];
  }

  async openWorkspace(workspaceId) {
    if (!this.pages.has(workspaceId)) this.pages.set(workspaceId, freshPage(BLANK_URL));
  }

  _page(workspaceId) {
    const page = this.pages.get(workspaceId);
    if (!page) throw new Error(`workspace ${workspaceId} has no open page`);
    return page;
  }

  _elements(page) {
    const site = SITE[page.url];
    if (!site) return [];
    return site.elements.map((element) => {
      const shown = { ...element, text: page.textOverrides[element.selector] ?? element.text };
      return {
        ...shown,
        handle: `h${element.selector.replace(/[^a-z0-9]/g, '')}`,
        value: element.isInput ? (page.values[element.selector] ?? '') : null,
        href: element.href ?? element.navigatesTo ?? null,
        formAction: element.formAction ?? null,
        digest: digestOf(shown),
      };
    });
  }

  _regionDigest(page, selector) {
    const members = SITE[page.url]?.regions?.[selector];
    if (!members) return null;
    const elements = this._elements(page).filter((element) => members.includes(element.selector));
    return sha256Hex(canonicalJson({
      selector,
      members: elements.map((element) => [element.digest, element.value]),
      mutation: page.regionMutations[selector] ?? 0,
    }));
  }

  async snapshot(workspaceId, { regions = [], regionGroups = [] } = {}) {
    const page = this._page(workspaceId);
    const site = SITE[page.url] ?? { title: '', text: '' };
    return {
      url: page.url,
      title: site.title,
      text: site.text,
      isTruncated: false,
      elements: this._elements(page),
      pageCount: 1,
      contentHash: sha256Hex(canonicalJson({
        url: page.url,
        values: page.values,
        mutation: page.mutation,
        textOverrides: page.textOverrides,
      })),
      regionDigests: Object.fromEntries([...regions, ...regionGroups].map((selector) => [selector, this._regionDigest(page, selector)])),
      regionOutlines: Object.fromEntries([...regions, ...regionGroups].map((selector) => [selector,
        (SITE[page.url]?.regions?.[selector] ?? []).map((member) => `[h${member.replace(/[^a-z0-9]/g, '')}]`).join(' | ')])),
    };
  }

  async probeUrl(workspaceId) {
    return this._page(workspaceId).url;
  }

  async probeElement(workspaceId, selector) {
    const matches = this._elements(this._page(workspaceId)).filter((element) => element.selector === selector);
    if (matches.length !== 1) return { count: matches.length, digest: null, text: null, value: null };
    const [element] = matches;
    return { count: 1, digest: element.digest, text: element.text, value: element.value };
  }

  /** Simulate human or page activity between observation and dispatch, optionally inside a region. */
  mutate(workspaceId, region = null) {
    const page = this._page(workspaceId);
    page.mutation += 1;
    if (region) page.regionMutations[region] = (page.regionMutations[region] ?? 0) + 1;
  }

  /** Change an element's text, as a page script replacing a control would. */
  changeText(workspaceId, selector, text) {
    this._page(workspaceId).textOverrides[selector] = text;
  }

  /** Hold the next effect in flight until the returned release function is called. */
  holdNext() {
    let release;
    const gate = new Promise((resolve) => {
      release = resolve;
    });
    this.held = gate;
    return release;
  }

  failNext(message) {
    this.nextFailure = message;
  }

  receipts() {
    if (!existsSync(this.receiptsPath)) return [];
    return readFileSync(this.receiptsPath, 'utf8').trim().split('\n').filter(Boolean).map((line) => JSON.parse(line));
  }

  async execute(workspaceId, request) {
    const page = this._page(workspaceId);
    this.executions.push(request.actionId);
    if (this.held) {
      const gate = this.held;
      this.held = null;
      await gate;
    }
    if (this.nextFailure) {
      const message = this.nextFailure;
      this.nextFailure = null;
      throw new Error(message);
    }
    if (request.kind === 'navigate') {
      this.pages.set(workspaceId, freshPage(request.target.url));
      return { finalUrl: request.target.url };
    }
    const element = this._elements(page).find((candidate) => candidate.selector === request.target.selector);
    if (!element) throw new Error(`no element ${request.target.selector}`);
    if (request.kind === 'fill') {
      page.values[element.selector] = request.params.value;
      return { selector: element.selector };
    }
    if (request.kind === 'download') {
      return { byteLength: element.downloads.length, sha256: sha256Hex(element.downloads) };
    }
    if (element.submitsTo) {
      appendFileSync(this.receiptsPath, `${JSON.stringify({
        actionId: request.actionId,
        effectKey: request.effect?.effectKey ?? null,
        externalIdempotencyKey: request.effect?.externalIdempotencyKey ?? null,
        values: page.values,
      })}\n`);
      this.pages.set(workspaceId, freshPage(element.submitsTo));
      return { selector: element.selector };
    }
    if (element.navigatesTo) this.pages.set(workspaceId, freshPage(element.navigatesTo));
    return { selector: element.selector };
  }

  async close() {
    this.pages.clear();
  }
}

export { FOREIGN_ORIGIN, FakeAdapter, ORIGIN };
