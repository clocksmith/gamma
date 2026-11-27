// The Forgejo commit authority (src/adapters/forgejo-merge-authority.js): approvals per screen, the
// live lock and stored record read from Forgejo's API (fake fetch with Forgejo 17.0.2 response
// shapes), the merge request rule against a merge body captured from Forgejo 17.0.2 in Chrome, and
// the service commit gate refusing a merge whose base branch changed after approval.
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import {
  NO_COMMIT_HERE, createForgejoMergeAuthority, mergeRequestRule, mergeTerms, predicateOf,
} from '../../src/adapters/forgejo-merge-authority.js';
import { collectObservedFacts } from '../../src/client/repair-boundary.js';
import { loadServiceConfig } from '../../src/config.js';
import { checkWriteRequest, matchFollowUp } from '../../src/request-guard.js';
import { WorkspaceService } from '../../src/service.js';
import { checkLiveLock, checkWriteBinding, validApproval } from '../../src/write-binding.js';
import { createOwnerSession, findElement } from '../../src/workflows/owner-session.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';
import { FORM_INTENT, WORKSPACE_ID, createClock } from '../support/harness.js';

const UI = 'http://forge.test';
const API = 'http://forge-api.test';
const REPO = 'ana/transfer-pilot';
const HEAD = '7242e1794df2813e330ec3cc1bce9e79eeb7c13a';
const TIP = '695a5669199f5ec4e10789fd343bfe81be2f1aa5';
const MERGED = 'a8fbad87bd3a3a9e8f5a076f0bce6f380b51db89';
const TOKEN = 'read-only-token';

/** An in-memory Forgejo answering the GET routes the authority reads, in Forgejo 17.0.2's shapes. */
function fakeForgejo() {
  const state = {
    pull: { number: 3, state: 'open', merged: false, mergeable: true, merge_commit_sha: null, merged_by: null,
      base: { ref: 'main' }, head: { ref: 'pay-a-100-00', sha: HEAD } },
    repo: { full_name: REPO, allow_merge_commits: true, allow_squash_merge: true, allow_rebase: true, allow_rebase_explicit: true,
      allow_fast_forward_only_merge: true, default_merge_style: 'squash' },
    branches: { main: TIP, release: 'a9994df8193baee76b0c1e010ab93e258f129b3f', 'pay-a-100-00': HEAD },
    commits: {},
    requests: [],
  };
  const fetch = async (url, init) => {
    state.requests.push({ url, method: init.method, auth: init.headers.Authorization });
    const path = new URL(url).pathname.replace('/api/v1', '');
    const json = body => ({ ok: true, status: 200, json: async () => structuredClone(body) });
    if (init.method !== 'GET' || init.headers.Authorization !== `token ${TOKEN}`) return { ok: false, status: 403, json: async () => ({}) };
    if (path === `/repos/${REPO}/pulls/3`) return json(state.pull);
    if (path === `/repos/${REPO}`) return json(state.repo);
    const branch = path.match(new RegExp(`^/repos/${REPO}/branches/(.+)$`));
    if (branch && state.branches[decodeURIComponent(branch[1])]) return json({ name: branch[1], commit: { id: state.branches[decodeURIComponent(branch[1])] } });
    const commit = path.match(new RegExp(`^/repos/${REPO}/git/commits/([a-f0-9]+)$`));
    if (commit && state.commits[commit[1]]) return json(state.commits[commit[1]]);
    return { ok: false, status: 404, json: async () => ({}) };
  };
  // What a merge commit (Create merge commit, branch kept) leaves in Forgejo's records.
  const merge = ({ parents = [TIP, HEAD] } = {}) => {
    Object.assign(state.pull, { state: 'closed', merged: true, mergeable: false, merge_commit_sha: MERGED, merged_by: { login: 'ben' } });
    state.commits[MERGED] = { sha: MERGED, parents: parents.map(sha => ({ sha })) };
    state.branches[state.pull.base.ref] = MERGED;
  };
  return { state, fetch, merge };
}

const SCREENS = [
  { url: `${UI}/${REPO}/pulls`, clicks: ['#pull-3-link'] },
  { url: `${UI}/${REPO}/pulls/3`, clicks: ['#style-toggle', '#style-merge', '#merge-open'], commit: '#merge-submit' },
];
const approveFor = (authority, extra = {}) => authority.approve({ approvalId: 'merge-3', uiOrigin: UI, repo: REPO, pr: 3, head: HEAD,
  base: 'main', baseTip: TIP, mergedBy: 'ben', screens: SCREENS, ...extra });

test('approvals: one per screen, the same lock, the commit and request rule only on the pull-request screen', async () => {
  const forge = fakeForgejo();
  const authority = createForgejoMergeAuthority({ apiOrigin: API, token: TOKEN, fetch: forge.fetch });
  const [list, page] = approveFor(authority);
  for (const approval of [list, page]) assert.equal(validApproval(approval), true);
  assert.deepEqual(list.lock, page.lock);
  assert.deepEqual(page.lock, { account: REPO, recordId: `${REPO}#3`, predicate: 'open-mergeable', recordVersion: HEAD,
    termsSha256: mergeTerms({ base: 'main', head: HEAD, style: 'merge' }) });
  assert.equal(list.commit, NO_COMMIT_HERE);
  assert.equal(list.request, undefined);
  assert.equal(page.commit, '#merge-submit');
  assert.deepEqual(page.request, mergeRequestRule({ uiOrigin: UI, repo: REPO, pr: 3 }));
  assert.deepEqual(page.readBack, { state: 'closed', merged: true, base: 'main', mergedBy: 'ben', mergeParents: [TIP, HEAD],
    baseAtMergeCommit: true, headBranchAt: HEAD });
  // The host returns the approval for the screen the write is on, by exact URL (and cited id).
  assert.equal(await authority.approvalFor({ url: `${UI}/${REPO}/pulls/3` }), page);
  assert.equal(await authority.approvalFor({ url: `${UI}/${REPO}/pulls` }), list);
  assert.equal(await authority.approvalFor({ url: `${UI}/${REPO}/pulls/3`, approvalId: 'merge-3/1' }), page);
  assert.equal(await authority.approvalFor({ url: `${UI}/${REPO}/pulls/3`, approvalId: 'merge-3/0' }), null);
  assert.equal(await authority.approvalFor({ url: `${UI}/${REPO}/pulls/4` }), null);
  // Clicks are bound per screen: the merge submit is not approved on the list.
  assert.deepEqual(checkWriteBinding(page, { url: page.target.url, method: 'submit', field: '#merge-submit' }), { ok: true });
  assert.equal(checkWriteBinding(page, { url: page.target.url, method: 'click', field: '#merge-submit' }).reason, 'approved-method-changed');
  assert.equal(checkWriteBinding(list, { url: list.target.url, method: 'submit', field: '#merge-submit' }).reason, 'approved-target-changed');
  assert.deepEqual(checkWriteBinding(list, { url: list.target.url, method: 'click', field: '#pull-3-link' }), { ok: true });
  assert.equal(checkWriteBinding(page, { url: page.target.url, method: 'click', field: '#delete-branch' }).reason, 'approved-target-changed');
  // Malformed approvals are refused when built.
  assert.throws(() => approveFor(authority, { head: 'abc' }), /needs an id/);
  assert.throws(() => approveFor(authority, { style: 'octopus' }), /needs an id/);
  assert.throws(() => approveFor(authority, { approvalId: 'two', screens: [SCREENS[1], { ...SCREENS[0], commit: '#x' }] }), /Exactly one screen/);
  assert.throws(() => approveFor(authority, { approvalId: 'dup', screens: [SCREENS[1], { url: SCREENS[1].url, clicks: [] }] }), /One approval per screen/);
  assert.throws(() => createForgejoMergeAuthority({ apiOrigin: API, token: '' }), /read-only Forgejo token/);
});

test('readLock: base, head, style, state and mergeability changes all change the lock', async () => {
  const forge = fakeForgejo();
  const authority = createForgejoMergeAuthority({ apiOrigin: API, token: TOKEN, fetch: forge.fetch });
  const [, page] = approveFor(authority);
  const lock = () => authority.readLock({ approval: page });
  assert.deepEqual(checkLiveLock(page, await lock()), { ok: true });
  assert.deepEqual(forge.state.requests.map(r => [r.method, new URL(r.url).pathname]),
    [['GET', `/api/v1/repos/${REPO}/pulls/3`], ['GET', `/api/v1/repos/${REPO}`]]);
  // Case 3 of the pilot: the base is changed to release through Forgejo's API; nothing else moves.
  forge.state.pull.base.ref = 'release';
  assert.deepEqual(checkLiveLock(page, await lock()), { ok: false, reason: 'approval-lock-changed', changed: ['termsSha256'] });
  forge.state.pull.base.ref = 'main';
  forge.state.pull.head.sha = 'b'.repeat(40);
  assert.deepEqual(checkLiveLock(page, await lock()).changed, ['recordVersion', 'termsSha256']);
  forge.state.pull.head.sha = HEAD;
  forge.state.repo.allow_merge_commits = false;
  assert.deepEqual(checkLiveLock(page, await lock()).changed, ['termsSha256']);
  forge.state.repo.allow_merge_commits = true;
  forge.state.pull.mergeable = false;
  assert.deepEqual(checkLiveLock(page, await lock()).changed, ['predicate']);
  forge.state.pull.mergeable = true;
  forge.merge();
  assert.deepEqual(checkLiveLock(page, await lock()).changed, ['predicate', 'recordVersion']);
  assert.equal(await authority.readLock({ approval: { approvalId: 'unknown' } }), null);
  assert.equal(predicateOf({ state: 'closed', merged: false }), 'closed');
  // Only GET requests, always with the read-only token.
  assert.ok(forge.state.requests.every(r => r.method === 'GET' && r.auth === `token ${TOKEN}`));
});

test('readRecord: the version moves to the merge commit and the stored merge reads back exactly', async () => {
  const forge = fakeForgejo();
  const authority = createForgejoMergeAuthority({ apiOrigin: API, token: TOKEN, fetch: forge.fetch });
  const [, page] = approveFor(authority);
  const before = await authority.readRecord({ approval: page });
  assert.equal(before.recordVersion, page.lock.recordVersion);
  assert.deepEqual(before.fields, { state: 'open', merged: false, base: 'main', mergedBy: null, mergeParents: null,
    baseAtMergeCommit: false, headBranchAt: HEAD });
  forge.merge();
  const after = await authority.readRecord({ approval: page });
  assert.equal(after.recordVersion, MERGED);
  assert.deepEqual(after.fields, page.readBack);
  // A squash (one parent) or a deleted head branch does not read back as the approved merge.
  const squash = fakeForgejo();
  const other = createForgejoMergeAuthority({ apiOrigin: API, token: TOKEN, fetch: squash.fetch });
  const [, approved] = approveFor(other);
  squash.merge({ parents: [TIP] });
  delete squash.state.branches['pay-a-100-00'];
  const fields = (await other.readRecord({ approval: approved })).fields;
  assert.deepEqual(fields.mergeParents, [TIP]);
  assert.equal(fields.headBranchAt, null);
});

test('fact roles: role pull keeps only booleans, and says whether base, head and terms are the approved ones', async () => {
  const forge = fakeForgejo();
  const authority = createForgejoMergeAuthority({ apiOrigin: API, token: TOKEN, fetch: forge.fetch });
  const [, page] = approveFor(authority);
  assert.deepEqual(authority.factRoles, ['pull']);
  const facts = async () => collectObservedFacts((await authority.readServerRoles(page, ['pull'])).responses).facts;
  assert.deepEqual({ ...await facts() }, { 'pull:/open': true, 'pull:/merged': false, 'pull:/mergeable': true,
    'pull:/base_approved': true, 'pull:/head_approved': true, 'pull:/terms_approved': true });
  forge.state.pull.base.ref = 'release';
  const changed = await facts();
  assert.equal(changed['pull:/base_approved'], false);
  assert.equal(changed['pull:/terms_approved'], false);
  assert.deepEqual(await authority.readServerRoles(page, ['comments']), { reads: 0, responses: [] });
  assert.equal((await authority.readServerRoles(page)).reads, 2);
});

// One merge request captured from Forgejo 17.0.2 (Chrome 146, CDP Fetch, request stage) after
// choosing "Create merge commit" on a repository whose default style is squash. Forgejo 17 sends
// no _csrf field; the boundary is new on every request. The default title is the squash-style one.
const CAPTURED = { url: `${UI}/${REPO}/pulls/3/merge`, boundary: '----WebKitFormBoundaryvTxo0zlE9AmAyBxX', parts: [
  ['head_commit_id', HEAD], ['merge_when_checks_succeed', 'false'], ['force_merge', 'false'],
  ['merge_title_field', 'Pay Test Vendor A 100.00 (#3)'], ['merge_message_field', `Reviewed-on: ${UI}/${REPO}/pulls/3\r\n`], ['do', 'merge']] };
function captured({ parts = CAPTURED.parts, url = CAPTURED.url, boundary = CAPTURED.boundary } = {}) {
  const body = parts.map(([name, value]) => `--${boundary}\r\nContent-Disposition: form-data; name="${name}"\r\n\r\n${value}\r\n`).join('')
    + `--${boundary}--\r\n`;
  return { method: 'POST', url, headers: { 'Content-Type': `multipart/form-data; boundary=${boundary}` },
    postDataEntries: [{ bytes: Buffer.from(body).toString('base64') }] };
}
const replace = (name, value) => CAPTURED.parts.map(([key, old]) => [key, key === name ? value : old]);

test('merge request rule: the captured Forgejo merge passes; style, extra field, target, version and follow-up are exact', () => {
  const rule = mergeRequestRule({ uiOrigin: UI, repo: REPO, pr: 3 });
  assert.deepEqual(checkWriteRequest(rule, HEAD, captured()), { ok: true, write: true });
  assert.deepEqual(checkWriteRequest(rule, HEAD, captured({ boundary: '----WebKitFormBoundaryOqGCYwOc1hVZu7lo' })), { ok: true, write: true });
  // Edited title and message are free; an older release's _csrf field is allowed.
  assert.equal(checkWriteRequest(rule, HEAD, captured({ parts: replace('merge_title_field', 'Other title') })).ok, true);
  assert.equal(checkWriteRequest(rule, HEAD, captured({ parts: [['_csrf', 'per-session'], ...CAPTURED.parts] })).ok, true);
  for (const style of ['squash', 'rebase', 'rebase-merge', 'fast-forward-only', 'manually-merged']) {
    assert.deepEqual(checkWriteRequest(rule, HEAD, captured({ parts: replace('do', style) })), { ok: false, reason: 'request-payload-mismatch', path: 'do' });
  }
  assert.deepEqual(checkWriteRequest(rule, HEAD, captured({ parts: [...CAPTURED.parts, ['delete_branch_after_merge', 'on']] })),
    { ok: false, reason: 'request-payload-mismatch', extra: ['delete_branch_after_merge'] });
  assert.equal(checkWriteRequest(rule, HEAD, captured({ parts: replace('force_merge', 'true') })).reason, 'request-payload-mismatch');
  assert.equal(checkWriteRequest(rule, HEAD, captured({ parts: replace('merge_when_checks_succeed', 'true') })).reason, 'request-payload-mismatch');
  assert.equal(checkWriteRequest(rule, HEAD, captured({ url: `${UI}/${REPO}/pulls/2/merge` })).reason, 'unexpected-write');
  assert.equal(checkWriteRequest(rule, HEAD, captured({ parts: replace('head_commit_id', 'c'.repeat(40)) })).reason, 'request-version-mismatch');
  // The merge request carries no base branch: a base changed after approval is the lock's to catch.
  assert.equal(CAPTURED.parts.some(([name]) => /base|target|branch/.test(name)), false);
  // The page's follow-up redirect, exact.
  const redirect = path => ({ method: 'POST', url: `${UI}/-/fetch-redirect`, headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    postData: new URLSearchParams({ redirect: path }).toString() });
  assert.equal(matchFollowUp(rule, redirect(`/${REPO}/pulls/3`)), 0);
  assert.equal(matchFollowUp(rule, redirect(`/${REPO}/pulls/2`)), -1);
});

/** The fixture form stands in for the pull-request page: its Send button is the merge submit. */
class MergePageAdapter extends FakeAdapter {
  constructor(options, forge) {
    super(options);
    this.forge = forge;
    this.supportsRequestGuard = true;
    this.guarded = [];
  }

  async execute(workspaceId, request, uploads) {
    if (request.target?.selector === '#send') {
      // A real adapter holds the page's requests; here the merge either reaches Forgejo or not.
      this.guarded.push(request.requestGuard ?? null);
      if (request.requestGuard) this.forge.merge();
      const effect = await super.execute(workspaceId, request, uploads);
      return { ...effect, requestGuard: { admitted: 1, blocked: [], decisions: [{ outcome: 'continued' }] } };
    }
    return super.execute(workspaceId, request, uploads);
  }
}

async function openGate(forge) {
  const root = mkdtempSync(join(tmpdir(), 'forgejo-authority-'));
  const base = loadServiceConfig();
  const config = { ...base, dispatch: { ...base.dispatch, completionTimeoutMs: 60, completionPollMs: 5, valueSettleMs: 10 } };
  const authority = createForgejoMergeAuthority({ apiOrigin: API, token: TOKEN, fetch: forge.fetch });
  authority.approve({ approvalId: 'merge-3', uiOrigin: UI, repo: REPO, pr: 3, head: HEAD, base: 'main', baseTip: TIP, mergedBy: 'ben',
    screens: [{ url: `${ORIGIN}/other`, clicks: ['#back'] }, { url: `${ORIGIN}/form`, clicks: [], commit: '#send' }] });
  let adapter = null;
  const service = await WorkspaceService.open({ stateDir: join(root, 'state'), config, clock: createClock().now,
    createAdapter: () => (adapter = new MergePageAdapter({ receiptsPath: join(root, 'receipts.jsonl') }, forge)), commitAuthority: authority });
  const { adminCredential } = await service.createWorkspace({ workspaceId: WORKSPACE_ID });
  await service.grantAuthorization({ workspaceId: WORKSPACE_ID, adminCredential, grantId: 'grant-agent', ownerId: 'agent',
    intents: [FORM_INTENT], actionKinds: ['navigate', 'click', 'submit'], targetOrigins: [ORIGIN] });
  const owner = await service.assignOwner({ workspaceId: WORKSPACE_ID, adminCredential, ownerId: 'agent' });
  const session = createOwnerSession(service, { workspaceId: WORKSPACE_ID, ...owner });
  const step = async (actionId, kind, target, extra = {}) => session.act(await session.observe(),
    { actionId, authorizedIntent: FORM_INTENT, kind, target, ...extra }).catch(error => ({ refusal: error.message }));
  const click = async (actionId, selector, kind = 'click') => {
    const obs = await session.observe();
    return step(actionId, kind, findElement(obs, element => element.selector === selector, selector),
      kind === 'submit' ? { completion: { completedWhen: [{ kind: 'element-present', selector: '#receipt' }] } } : {});
  };
  return { step, click, adapter: () => adapter, close: async () => { await service.close(); rmSync(root, { recursive: true, force: true }); } };
}
const refusalOf = result => result.refusal ?? result.neverDispatched?.detail ?? '';

test('service gate: the approved merge is verified from Forgejo\'s records; a base changed after approval is never dispatched', async () => {
  const forge = fakeForgejo();
  const gate = await openGate(forge);
  try {
    await gate.step('nav', 'navigate', { url: `${ORIGIN}/other` });
    const back = await gate.click('back', '#back');
    assert.equal(back.outcome, 'completed');
    const merged = await gate.click('merge', '#send', 'submit');
    assert.equal(merged.outcome, 'completed');
    assert.equal(merged.outcomeBasis, 'commit-verified');
    // The adapter was handed the merge request rule, with the approved head as the version.
    const [guard] = gate.adapter().guarded;
    assert.equal(guard.version, HEAD);
    assert.deepEqual(guard.rule, mergeRequestRule({ uiOrigin: UI, repo: REPO, pr: 3 }));
  } finally { await gate.close(); }

  // Case 3: base changed to release after approval. Every click on an approved screen re-reads the
  // lock, so the navigation click is refused already and the merge never reaches the adapter.
  const moved = fakeForgejo();
  moved.state.pull.base.ref = 'release';
  const refused = await openGate(moved);
  try {
    await refused.step('nav', 'navigate', { url: `${ORIGIN}/other` });
    assert.match(refusalOf(await refused.click('back', '#back')), /approval-lock-changed at admission/);
    await refused.step('nav-form', 'navigate', { url: `${ORIGIN}/form` });
    assert.match(refusalOf(await refused.click('merge', '#send', 'submit')), /approval-lock-changed at admission/);
    assert.deepEqual(refused.adapter().guarded, []);
    assert.equal(moved.state.pull.merged, false);
  } finally { await refused.close(); }
});
