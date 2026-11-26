// Fawn workspace — write approval bindings
//
// Pure helpers for WorkspaceService #commitVerifiedWrite: the shape of a host-held approval and
// the comparison of one write against it. No I/O and no authority of its own; guard advice is
// read separately and can only lower a write to a refusal.

import { expectedBodyFields } from './client/branch-verifier.js';
import { canonicalJson, sha256Hex } from './journal.js';
import { validRequestRule } from './request-guard.js';

// Kinds that can change a record. navigate and download only read.
const WRITE_KINDS = new Set(['fill', 'select', 'click', 'submit', 'upload']);
// The live lock an approval binds; each field must still equal the approved one.
const LOCK_FIELDS = Object.freeze(['account', 'recordId', 'predicate', 'recordVersion', 'termsSha256']);
const HASH = /^[a-f0-9]{64}$/;
const plainObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const scalarId = value => (typeof value === 'string' && value.length > 0) || Number.isSafeInteger(value);
const refusal = (reason, details = {}) => Object.freeze({ ok: false, reason, ...details });
const OK = Object.freeze({ ok: true });

function href(url) {
  try { return new URL(url).href; } catch { return null; }
}

function canonicalBody(payload, kind) {
  if (kind === 'none') return null;
  if (kind === 'text') return payload;
  if (kind === 'json') return typeof payload === 'string' ? JSON.parse(payload) : JSON.parse(JSON.stringify(payload));
  const entries = [...(typeof payload === 'string' ? new URLSearchParams(payload) : payload).entries()];
  if (entries.some(([, value]) => typeof value !== 'string')) return undefined;
  return entries.sort((x, y) => (x[0] < y[0] ? -1 : x[0] > y[0] ? 1 : x[1] < y[1] ? -1 : x[1] > y[1] ? 1 : 0));
}

/**
 * SHA-256 binding of a write payload, or null when it cannot be pinned. `expectedBodyFields`
 * (whose per-field digests are the 64-bit `digestValue`) only classifies the body and refuses
 * opaque or truncated ones; the binding itself is SHA-256 over the canonical body.
 */
function payloadDigest(payload) {
  const shape = expectedBodyFields(payload);
  if (shape.kind === 'opaque' || shape.truncated) return null;
  const body = canonicalBody(payload, shape.kind);
  return body === undefined ? null : sha256Hex(canonicalJson({ kind: shape.kind, body }));
}

/**
 * Builds the approval a person (or trusted host policy) grants for one commit. Called by the
 * approver, never by a guard. `fields` maps each page field to the exact value to fill; `commit`
 * is the control that sends the write; `readBack` is the exact stored state afterwards.
 * `versionToken` ({ selector, value }), when given, names the page element holding the form's
 * optimistic-concurrency value (the version the save sends); `value` is the approved record version.
 * `request` ({ method, url, fields, versionPath, allowPaths? }), when given, is the one write request
 * the commit may send; the adapter holds the page's requests and admits only a match, with the
 * approved record version at `versionPath` in the body.
 */
function approveCommit({ approvalId, target, lock, fields, clicks = [], commit, commitMethod = 'submit', readBack, versionToken, request }) {
  const actions = [
    ...Object.entries(fields ?? {}).map(([field, value]) => ({ method: 'fill', field, payloadSha256: payloadDigest({ value }) })),
    ...clicks.map(field => ({ method: 'click', field, payloadSha256: payloadDigest(null) })),
    { method: commitMethod, field: commit, payloadSha256: payloadDigest(null) },
  ];
  const approval = structuredClone({ approvalId, target: { ...target, url: href(target?.url) }, lock, fields, actions, commit, readBack,
    ...(versionToken !== undefined ? { versionToken } : {}), ...(request !== undefined ? { request } : {}) });
  if (!validApproval(approval)) throw Error('An approval needs a target, a live lock, exact field values, a commit control and a read-back');
  return Object.freeze(approval);
}

function validApproval(approval) {
  if (!plainObject(approval) || typeof approval.approvalId !== 'string' || !approval.approvalId) return false;
  const { target, lock, fields, actions, commit, readBack, versionToken, request } = approval;
  // An optional request rule: the one write the commit may send (see request-guard.js).
  if (request !== undefined && !validRequestRule(request)) return false;
  if (!plainObject(target) || href(target.url) !== target.url || typeof target.entity !== 'string' || !target.entity
    || !scalarId(target.rowId)) return false;
  if (!plainObject(lock) || !LOCK_FIELDS.every(key => scalarId(lock[key])) || lock.recordId !== target.rowId) return false;
  // An optional version token names the page element carrying the form's concurrency value. It must
  // carry the approved record version itself, so the server's check and the lock name one version.
  if (versionToken !== undefined && (!plainObject(versionToken) || typeof versionToken.selector !== 'string'
    || !versionToken.selector || versionToken.value !== String(lock.recordVersion))) return false;
  if (!plainObject(fields) || !Array.isArray(actions) || typeof commit !== 'string'
    || !plainObject(readBack) || Object.keys(readBack).length === 0) return false;
  if (!actions.every(action => plainObject(action) && WRITE_KINDS.has(action.method)
    && typeof action.field === 'string' && HASH.test(action.payloadSha256 ?? ''))) return false;
  // Every exact page value is also an approved fill of that value, and the commit is an approved action.
  return Object.entries(fields).every(([field, value]) => typeof value === 'string' && actions.some(action =>
    action.method === 'fill' && action.field === field && action.payloadSha256 === payloadDigest({ value })))
    && actions.some(action => action.field === commit && action.method !== 'fill');
}

/** Target URL, field, method and payload of one write against the approval. */
function checkWriteBinding(approval, { url, method, field, payload = null }) {
  if (href(url) !== approval.target.url) return refusal('approved-target-changed', { changed: ['url'] });
  const onField = approval.actions.filter(action => action.field === field);
  if (onField.length === 0) return refusal('approved-target-changed', { changed: ['field'] });
  const withMethod = onField.filter(action => action.method === method);
  if (withMethod.length === 0) return refusal('approved-method-changed');
  const digest = payloadDigest(payload);
  if (digest === null) return refusal('payload-unreadable');
  return withMethod.some(action => action.payloadSha256 === digest) ? OK : refusal('approved-payload-changed');
}

/** The live record identity and lock, read from the system of record, against the approval. */
function checkLiveLock(approval, live) {
  if (!plainObject(live)) return refusal('live-lock-unavailable');
  const target = [['entity', approval.target.entity, live.entity], ['rowId', approval.target.rowId, live.recordId]]
    .filter(([, approved, current]) => approved !== current).map(([key]) => key);
  if (target.length) return refusal('approved-target-changed', { changed: target });
  const changed = LOCK_FIELDS.filter(key => live[key] !== approval.lock[key]);
  return changed.length ? refusal('approval-lock-changed', { changed }) : OK;
}

/** Guard output that recommends stopping. Nothing a guard returns can authorize a write. */
function adviceAbstains(advice) {
  return advice === false || advice?.status === 'abstain' || advice?.decision === 'abstain' || advice?.tool === 'ask_human';
}

export {
  LOCK_FIELDS,
  WRITE_KINDS,
  adviceAbstains,
  approveCommit,
  checkLiveLock,
  checkWriteBinding,
  payloadDigest,
  validApproval,
};
