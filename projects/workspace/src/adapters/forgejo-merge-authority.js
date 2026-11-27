// Fawn workspace — Forgejo commit authority for one pull-request merge
//
// The trusted host's side of WorkspaceService's commit gate ({ approvalFor, readLock, readRecord })
// for merging one Forgejo pull request through its web UI. It reads Forgejo's REST API (GET only)
// with a read-only token and never writes. Every screen the approved workflow clicks on gets its own
// approval with the same live lock; only the pull-request screen's approval names the commit and the
// one merge request the page may send (see request-guard.js).
//
// The lock binds the record (repository, pull-request number), the predicate open-and-mergeable, the
// head commit as record version (the merge form sends it as head_commit_id, so Forgejo itself refuses
// a moved head) and termsSha256 over base branch, head commit and merge style. Forgejo's merge request
// does not carry the base branch, so a base changed after approval is caught here, before dispatch.

import { canonicalJson, sha256Hex } from '../journal.js';
import { approveCommit } from '../write-binding.js';

const ENTITY = 'forgejo-pull-request';
const STYLES = Object.freeze({ merge: 'allow_merge_commits', rebase: 'allow_rebase', 'rebase-merge': 'allow_rebase_explicit',
  squash: 'allow_squash_merge', 'fast-forward-only': 'allow_fast_forward_only_merge' });
// Never matches a page selector: the commit of a screen that only navigates towards the merge.
const NO_COMMIT_HERE = 'forgejo-merge:commit-is-on-the-pull-request-screen';
// The fact role readServerRoles serves (live-lookahead.js, repair-boundary.js).
const FACT_ROLES = Object.freeze(['pull']);
const SHA = /^[a-f0-9]{40}([a-f0-9]{24})?$/;
const REPO = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;

const origin = url => new URL(url).origin;

/** sha256 over the merge's terms: base branch, head commit and merge style (null when not allowed). */
function mergeTerms({ base, head, style }) {
  return sha256Hex(canonicalJson({ schema: 'forgejo-merge-terms/v1', base, head, style }));
}

/** The predicate the lock binds: the state that allows the approved merge. */
function predicateOf(pull) {
  if (pull.merged) return 'merged';
  if (pull.state !== 'open') return 'closed';
  return pull.mergeable === true ? 'open-mergeable' : 'open-not-mergeable';
}

/** The one merge request the pull-request page sends, as a request-guard rule. */
function mergeRequestRule({ uiOrigin, repo, pr, style = 'merge' }) {
  const ui = origin(uiOrigin);
  return {
    method: 'POST',
    url: `${ui}/${repo}/pulls/${pr}/merge`,
    versionPath: 'head_commit_id',
    fields: { do: style, force_merge: 'false', merge_when_checks_succeed: 'false' },
    // The title and message are free (the default text); Forgejo 17 sends no _csrf field, older
    // releases did. No delete_branch_after_merge: the approved merge keeps the branch.
    allowPaths: ['_csrf', 'merge_title_field', 'merge_message_field'],
    // form-fetch-action posts the merge response's redirect back to the server once it answers.
    followUps: [{ method: 'POST', url: `${ui}/-/fetch-redirect`, fields: { redirect: `/${repo}/pulls/${pr}` } }],
  };
}

/**
 * A commit authority for one approved merge.
 *  - `apiOrigin`: where Forgejo's API is read; `token`: a read-only token (never logged).
 *  - `fetch`: injectable for tests.
 * `approve(...)` is the approver's call (a person or trusted host policy), never a guard's.
 */
function createForgejoMergeAuthority({ apiOrigin, token, fetch: fetchImpl = globalThis.fetch }) {
  if (typeof token !== 'string' || !token) throw Error('A read-only Forgejo token is required');
  const api = `${origin(apiOrigin)}/api/v1`;
  let reads = 0;
  const get = async path => {
    reads += 1;
    const response = await fetchImpl(`${api}${path}`, { method: 'GET', headers: { Authorization: `token ${token}`, Accept: 'application/json' } });
    if (!response.ok) throw Error(`GET ${path} -> ${response.status}`);
    return response.json();
  };
  const approvals = new Map();

  /** The pull request's live record, normalized; the same read every arm can be given. */
  async function readPullRequest(repo, pr) {
    const pull = await get(`/repos/${repo}/pulls/${pr}`);
    return { number: pull.number, state: pull.state, merged: pull.merged === true, mergeable: pull.mergeable === true,
      base: pull.base?.ref ?? null, headRef: pull.head?.ref ?? null, headSha: pull.head?.sha ?? null,
      mergeCommit: pull.merge_commit_sha ?? null, mergedBy: pull.merged_by?.login ?? null };
  }

  async function liveLock(merge) {
    const [pull, repository] = await Promise.all([readPullRequest(merge.repo, merge.pr), get(`/repos/${merge.repo}`)]);
    const style = repository[STYLES[merge.style]] === true ? merge.style : null;
    return { pull, lock: { entity: ENTITY, account: merge.repo, recordId: `${merge.repo}#${merge.pr}`, predicate: predicateOf(pull),
      recordVersion: pull.merged ? pull.mergeCommit : pull.headSha, termsSha256: mergeTerms({ base: pull.base, head: pull.headSha, style }) } };
  }

  /**
   * Approve one merge. `screens` are the pages the workflow clicks on, in any order: each
   * { url, clicks } where `clicks` are the selectors it may click there; the pull-request screen also
   * has `commit` (the merge form's submit button; `commitMethod` defaults to submit). `baseTip` is the base branch's commit at approval: the
   * merge commit's first parent must be it.
   */
  function approve({ approvalId, uiOrigin, repo, pr, head, base, baseTip, style = 'merge', mergedBy, screens }) {
    if (typeof approvalId !== 'string' || !approvalId || !REPO.test(repo ?? '') || !Number.isSafeInteger(pr) || pr < 1
      || !SHA.test(head ?? '') || !SHA.test(baseTip ?? '') || typeof base !== 'string' || !base || !STYLES[style]
      || typeof mergedBy !== 'string' || !mergedBy || !Array.isArray(screens) || screens.length === 0) {
      throw Error('A Forgejo merge approval needs an id, repository, pull request, head, base, base tip, style, merger and screens');
    }
    const commits = screens.filter(screen => typeof screen.commit === 'string');
    if (commits.length !== 1) throw Error('Exactly one screen holds the merge commit');
    const merge = { repo, pr, head, base, baseTip, style, mergedBy };
    const lock = { account: repo, recordId: `${repo}#${pr}`, predicate: 'open-mergeable', recordVersion: head,
      termsSha256: mergeTerms({ base, head, style }) };
    const readBack = { state: 'closed', merged: true, base, mergedBy, mergeParents: [baseTip, head], baseAtMergeCommit: true, headBranchAt: head };
    const built = screens.map((screen, index) => {
      const isCommit = typeof screen.commit === 'string';
      return approveCommit({ approvalId: `${approvalId}/${index}`, target: { url: screen.url, entity: ENTITY, rowId: lock.recordId }, lock,
        fields: {}, clicks: screen.clicks ?? [], commit: isCommit ? screen.commit : NO_COMMIT_HERE,
        commitMethod: isCommit ? screen.commitMethod ?? 'submit' : 'click', readBack,
        ...(isCommit ? { request: mergeRequestRule({ uiOrigin, repo, pr, style }) } : {}) });
    });
    if (new Set(built.map(approval => approval.target.url)).size !== built.length) throw Error('One approval per screen URL');
    for (const approval of built) approvals.set(approval.approvalId, { approval, merge });
    return built;
  }

  const held = approval => approvals.get(approval?.approvalId)?.merge ?? null;

  return {
    factRoles: FACT_ROLES,
    approve,
    readPullRequest,
    reads: () => reads,

    /** The host-held approval for the screen the write is on (exact URL), or null. */
    async approvalFor({ url, approvalId = null }) {
      for (const { approval } of approvals.values()) {
        if (approval.target.url === url && (approvalId === null || approval.approvalId === approvalId)) return approval;
      }
      return null;
    },

    /** The live lock from Forgejo's records: entity, account, record id, predicate, version, terms. */
    async readLock({ approval }) {
      const merge = held(approval);
      if (!merge) return null;
      return (await liveLock(merge)).lock;
    },

    /** The stored record after a commit: the version moves from the head to the merge commit. */
    async readRecord({ approval }) {
      const merge = held(approval);
      if (!merge) return null;
      const pull = await readPullRequest(merge.repo, merge.pr);
      const fields = { state: pull.state, merged: pull.merged, base: pull.base, mergedBy: pull.mergedBy, mergeParents: null,
        baseAtMergeCommit: false, headBranchAt: null };
      const encode = name => encodeURIComponent(name);
      if (pull.headRef) fields.headBranchAt = (await get(`/repos/${merge.repo}/branches/${encode(pull.headRef)}`).catch(() => null))?.commit?.id ?? null;
      if (pull.merged && pull.mergeCommit) {
        const commit = await get(`/repos/${merge.repo}/git/commits/${pull.mergeCommit}`);
        fields.mergeParents = (commit.parents ?? []).map(parent => parent.sha);
        fields.baseAtMergeCommit = (await get(`/repos/${merge.repo}/branches/${encode(pull.base)}`)).commit?.id === pull.mergeCommit;
      }
      return { account: merge.repo, recordId: `${merge.repo}#${merge.pr}`, recordVersion: pull.merged ? pull.mergeCommit : pull.headSha, fields };
    },

    /**
     * Server facts for the applicability check (repair-boundary.js collectObservedFacts keeps only
     * booleans and integers): role `pull` with the record's state and whether its base, head and
     * style are still the approved ones.
     */
    async readServerRoles(approval, roles = FACT_ROLES) {
      const merge = held(approval);
      if (!merge || !roles.every(role => FACT_ROLES.includes(role))) return { reads: 0, responses: [] };
      const before = reads;
      const { pull, lock } = await liveLock(merge);
      const json = { open: pull.state === 'open', merged: pull.merged, mergeable: pull.mergeable,
        base_approved: pull.base === merge.base, head_approved: pull.headSha === merge.head,
        terms_approved: lock.termsSha256 === mergeTerms({ base: merge.base, head: merge.head, style: merge.style }) };
      return { reads: reads - before, responses: roles.includes('pull')
        ? [{ sameOrigin: true, method: 'GET', transport: 'fetch', status: 200, sourceRole: 'pull', json }] : [] };
    },
  };
}

export { FACT_ROLES, NO_COMMIT_HERE, createForgejoMergeAuthority, mergeRequestRule, mergeTerms, predicateOf };
