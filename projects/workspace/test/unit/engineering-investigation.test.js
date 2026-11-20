// Unit tests for the engineering investigation workflow adapter: evidence capture, unauthorized
// link skipping, precondition guard, postmortem bundle export and interruption reconciliation.
import assert from 'node:assert/strict';
import { appendFileSync, existsSync, mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { canonicalJson, sha256Hex } from '../../src/journal.js';
import { createOwnerSession } from '../../src/workflows/owner-session.js';
import {
  investigationEffectKey,
  recoverEngineeringInvestigation,
  runEngineeringInvestigation,
} from '../../src/workflows/engineering-investigation.js';

const OPS_ORIGIN = 'https://ops.test';
const FOREIGN_ORIGIN = 'https://vendor.invalid';
const BUNDLE_TEXT = 'incident,42,duplicate-charge,mitigated\n';

function digestOf(element) {
  return sha256Hex(canonicalJson({ tag: element.tag, attributes: element.attributes, text: element.text }));
}

class IncidentFakeAdapter {
  constructor({ receiptsPath }) {
    this.receiptsPath = receiptsPath;
    this.pages = new Map();
    this.incidentStatus = 'open';
    this.auditEntries = [];
    this.auditMissing = false;
    this.failSubmitAfterReceipt = false;
    this.failSubmitBeforeReceipt = false;
  }

  async openWorkspace(workspaceId) {
    if (!this.pages.has(workspaceId)) this.pages.set(workspaceId, { url: 'about:blank', values: {} });
  }

  _site(url) {
    if (url === `${OPS_ORIGIN}/incidents/42`) {
      return {
        title: 'Incident 42: Duplicate checkout charge',
        text: `Incident 42 status: ${this.incidentStatus}\nSignal: retry timeout caused duplicate order charge`,
        elements: [
          { selector: '#status', tag: 'p', attributes: [['id', 'status']], text: this.incidentStatus },
          {
            selector: '#runbook-retry',
            tag: 'a',
            attributes: [['href', '/runbooks/retry-timeout'], ['id', 'runbook-retry']],
            text: 'Runbook: retry timeout idempotency',
            navigatesTo: `${OPS_ORIGIN}/runbooks/retry-timeout`,
          },
          {
            selector: '#vendor-link',
            tag: 'a',
            attributes: [['href', `${FOREIGN_ORIGIN}/retry-status`], ['id', 'vendor-link']],
            text: 'External vendor retry status',
            navigatesTo: `${FOREIGN_ORIGIN}/retry-status`,
          },
          { selector: '#root-cause', tag: 'input', attributes: [['id', 'root-cause'], ['name', 'rootCause']], text: '', isInput: true },
          { selector: '#mitigation', tag: 'input', attributes: [['id', 'mitigation'], ['name', 'mitigation']], text: '', isInput: true },
          {
            selector: '#resolve',
            tag: 'button',
            attributes: [['id', 'resolve'], ['type', 'submit']],
            text: 'Record mitigation',
            formAction: `${OPS_ORIGIN}/incidents/42/mitigate`,
            submitsTo: `${OPS_ORIGIN}/incidents/42/resolved`,
          },
        ],
      };
    }
    if (url === `${OPS_ORIGIN}/runbooks/retry-timeout`) {
      return {
        title: 'Retry timeout runbook',
        text: 'Verify gateway idempotency key before replaying checkout requests.\nUnrelated note.',
        elements: [],
      };
    }
    if (url === `${OPS_ORIGIN}/incidents/42/resolved`) {
      return {
        title: 'Incident 42 mitigated',
        text: 'Mitigation recorded for incident 42',
        elements: [
          { selector: '#confirmed', tag: 'p', attributes: [['id', 'confirmed']], text: 'Mitigation recorded' },
          {
            selector: '#bundle',
            tag: 'a',
            attributes: [['href', '/incidents/42/bundle.csv'], ['id', 'bundle']],
            text: 'Download postmortem bundle',
            href: `${OPS_ORIGIN}/incidents/42/bundle.csv`,
            downloads: BUNDLE_TEXT,
          },
        ],
      };
    }
    if (url === `${OPS_ORIGIN}/incidents/audit`) {
      return {
        title: 'Incident audit log',
        text: `Audit entries: ${this.auditEntries.join(' | ') || 'none'}`,
        elements: this.auditMissing ? [] : [{
          selector: '#audit-log',
          tag: 'div',
          attributes: [['id', 'audit-log']],
          text: this.auditEntries.join(' | ') || 'none',
        }],
      };
    }
    return { title: '', text: '', elements: [] };
  }

  _elements(page) {
    return this._site(page.url).elements.map((element) => ({
      ...element,
      handle: `h${element.selector.replace(/[^a-z0-9]/g, '')}`,
      value: element.isInput ? (page.values[element.selector] ?? '') : null,
      href: element.href ?? element.navigatesTo ?? null,
      formAction: element.formAction ?? null,
      digest: digestOf(element),
    }));
  }

  async snapshot(workspaceId) {
    const page = this.pages.get(workspaceId);
    const site = this._site(page.url);
    return {
      url: page.url,
      title: site.title,
      text: site.text,
      isTruncated: false,
      elements: this._elements(page),
      pageCount: 1,
      contentHash: sha256Hex(canonicalJson({ url: page.url, values: page.values, status: this.incidentStatus, audit: this.auditEntries })),
      regionDigests: {},
      regionOutlines: {},
    };
  }

  async probeUrl(workspaceId) {
    return this.pages.get(workspaceId).url;
  }

  async probeElement(workspaceId, selector) {
    const matches = this._elements(this.pages.get(workspaceId)).filter((element) => element.selector === selector);
    if (matches.length !== 1) return { count: matches.length, digest: null, text: null, value: null };
    const [element] = matches;
    return { count: 1, digest: element.digest, text: element.text, value: element.value };
  }

  receipts() {
    if (!existsSync(this.receiptsPath)) return [];
    return readFileSync(this.receiptsPath, 'utf8').trim().split('\n').filter(Boolean).map((line) => JSON.parse(line));
  }

  async execute(workspaceId, request) {
    const page = this.pages.get(workspaceId);
    if (request.kind === 'navigate') {
      this.pages.set(workspaceId, { url: request.target.url, values: {} });
      return { finalUrl: request.target.url };
    }
    const element = this._elements(page).find((candidate) => candidate.selector === request.target.selector);
    if (!element) throw new Error(`missing element ${request.target.selector}`);
    if (request.kind === 'fill') {
      page.values[element.selector] = request.params.value;
      return { selector: element.selector };
    }
    if (request.kind === 'download') {
      return { byteLength: element.downloads.length, sha256: sha256Hex(element.downloads) };
    }
    if (element.submitsTo) {
      if (this.failSubmitBeforeReceipt) {
        this.failSubmitBeforeReceipt = false;
        throw new Error('transport dropped before server receipt');
      }
      const summary = `${page.values['#root-cause']} ${page.values['#mitigation']}`;
      this.auditEntries.push(summary);
      appendFileSync(this.receiptsPath, `${JSON.stringify({ actionId: request.actionId, effectKey: request.effect?.effectKey, summary })}\n`);
      if (this.failSubmitAfterReceipt) {
        this.failSubmitAfterReceipt = false;
        throw new Error('connection reset after server committed mitigation');
      }
      this.pages.set(workspaceId, { url: element.submitsTo, values: {} });
      return { selector: element.selector };
    }
    if (element.navigatesTo) this.pages.set(workspaceId, { url: element.navigatesTo, values: {} });
    return { selector: element.selector };
  }

  async close() {
    this.pages.clear();
  }
}

async function openHarness() {
  const root = mkdtempSync(join(tmpdir(), 'fawn-eng-inv-'));
  let adapter;
  const service = await WorkspaceService.open({
    stateDir: join(root, 'service'),
    config: loadServiceConfig(),
    createAdapter: () => (adapter = new IncidentFakeAdapter({ receiptsPath: join(root, 'receipts.jsonl') })),
  });
  const workspaceId = 'ws-incident';
  const { adminCredential } = await service.createWorkspace({ workspaceId });
  await service.grantAuthorization({
    workspaceId,
    adminCredential,
    grantId: 'ops-grant',
    ownerId: 'investigator',
    intents: ['ops:investigate'],
    actionKinds: ['navigate', 'click', 'fill', 'submit', 'download'],
    targetOrigins: [OPS_ORIGIN],
  });
  const owner = await service.assignOwner({ workspaceId, adminCredential, ownerId: 'investigator' });
  const session = createOwnerSession(service, { workspaceId, ...owner });
  return { root, service, adapter, session, cleanup: async () => { await service.close(); rmSync(root, { recursive: true, force: true }); } };
}

const BASE_TASK = Object.freeze({
  intent: 'ops:investigate',
  incidentUrl: `${OPS_ORIGIN}/incidents/42`,
  signals: ['retry', 'idempotency'],
  maxRunbooks: 3,
  dispositionFields: {
    rootCause: 'Missing checkout retry idempotency check',
    mitigation: 'Enforce gateway idempotency token before retry',
  },
  preconditions: [{ kind: 'element-text-includes', selector: '#status', value: 'open' }],
  completedWhen: [{ kind: 'element-present', selector: '#confirmed' }],
  artifactUrl: `${OPS_ORIGIN}/incidents/42/resolved`,
  artifactLinkText: 'Download postmortem bundle',
  auditUrl: `${OPS_ORIGIN}/incidents/audit`,
  auditSelector: '#audit-log',
});

// 1. Clean execution: captures incident + authorized runbook, skips foreign origin, checks preconditions, exports bundle.
{
  const harness = await openHarness();
  try {
    const outcome = await runEngineeringInvestigation(harness.session, { ...BASE_TASK, runId: 'clean' });
    assert.equal(outcome.status, 'completed');
    assert.equal(outcome.effectKey, investigationEffectKey(BASE_TASK.incidentUrl, BASE_TASK.dispositionFields));
    assert.equal(outcome.evidence.length, 2);
    assert.equal(outcome.evidence[0].kind, 'incident');
    assert.equal(outcome.evidence[1].kind, 'runbook');
    assert.ok(outcome.evidence[1].passages[0].includes('idempotency'));
    assert.deepEqual(outcome.skipped, [{ href: `${FOREIGN_ORIGIN}/retry-status`, code: 'unauthorized-target' }]);
    assert.equal(outcome.artifact?.sha256, sha256Hex(BUNDLE_TEXT));
    assert.equal(harness.adapter.receipts().length, 1);
  } finally {
    await harness.cleanup();
  }
}

// 2. Stale incident status blocks submission before dispatch via preconditions; zero external effects.
{
  const harness = await openHarness();
  try {
    harness.adapter.incidentStatus = 'resolved-by-oncall';
    const outcome = await runEngineeringInvestigation(harness.session, { ...BASE_TASK, runId: 'stale' });
    assert.equal(outcome.status, 'never-dispatched');
    assert.equal(outcome.submission.neverDispatched.code, 'precondition-unestablished');
    assert.equal(harness.adapter.receipts().length, 0);
  } finally {
    await harness.cleanup();
  }
}

// 3. Uncertain submission where audit log confirms effect: reconciles effect-present without duplicate submission, then exports bundle.
{
  const harness = await openHarness();
  try {
    harness.adapter.failSubmitAfterReceipt = true;
    const interrupted = await runEngineeringInvestigation(harness.session, { ...BASE_TASK, runId: 'uncertain-present' });
    assert.equal(interrupted.status, 'unknown');
    assert.equal(harness.adapter.receipts().length, 1);

    const recovered = await recoverEngineeringInvestigation(harness.session, { ...BASE_TASK, runId: 'uncertain-present' });
    assert.equal(recovered.status, 'completed');
    assert.equal(recovered.recovered, 'application-state');
    assert.equal(recovered.artifact?.sha256, sha256Hex(BUNDLE_TEXT));
    assert.equal(harness.adapter.receipts().length, 1, 'Reconciliation must never duplicate an already-recorded mitigation');
  } finally {
    await harness.cleanup();
  }
}

// 4. Uncertain submission where audit log positively excludes effect: reconciles effect-absent and resubmits once with provenance.
{
  const harness = await openHarness();
  try {
    harness.adapter.failSubmitBeforeReceipt = true;
    const interrupted = await runEngineeringInvestigation(harness.session, { ...BASE_TASK, runId: 'uncertain-absent' });
    assert.equal(interrupted.status, 'unknown');
    assert.equal(harness.adapter.receipts().length, 0);

    const recovered = await recoverEngineeringInvestigation(harness.session, { ...BASE_TASK, runId: 'uncertain-absent' });
    assert.equal(recovered.status, 'completed');
    assert.equal(recovered.recovered, 'resubmitted-after-absence');
    assert.equal(recovered.artifact?.sha256, sha256Hex(BUNDLE_TEXT));
    assert.equal(harness.adapter.receipts().length, 1);
  } finally {
    await harness.cleanup();
  }
}

// 5. Uncertain submission with inconclusive audit page stops for human review without retrying.
{
  const harness = await openHarness();
  try {
    harness.adapter.failSubmitBeforeReceipt = true;
    harness.adapter.auditMissing = true;
    await runEngineeringInvestigation(harness.session, { ...BASE_TASK, runId: 'uncertain-inconclusive' });
    const recovered = await recoverEngineeringInvestigation(harness.session, { ...BASE_TASK, runId: 'uncertain-inconclusive' });
    assert.equal(recovered.status, 'unknown');
    assert.equal(recovered.recovered, 'human-review-needed');
    assert.equal(harness.adapter.receipts().length, 0);
  } finally {
    await harness.cleanup();
  }
}

console.log('ok: engineering-investigation workflow evidence, foreign-origin skip, precondition guard, bundle export and reconciliation');
