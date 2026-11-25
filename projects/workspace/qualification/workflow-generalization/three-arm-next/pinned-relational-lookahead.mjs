#!/usr/bin/env node
// Digest-Pinned Relational Live-Lookahead Coordinator (`pinned-relational-lookahead.mjs`).
//
// Bridges `adaptive-relational-guard.mjs` with Fawn's `branch-verifier.js` (`branchExpression`,
// `parseBranchResult`, `decideBranch`) WITHOUT modifying `src/client/*` and WITHOUT letting raw
// page values leave sealed browser branches:
//   1. Pre-branch Adaptive Relational Guard (`evaluateRoute`):
//      Checks typed relational invariants (`set` `subset-of`, `intervals-within`, `kmap-lte`,
//      cross-role `ref`/`sym` bindings) sequentially before spawning any browser branch.
//   2. Privacy-Preserving Outbound Body Digest Pinning (`computeExpectedBranchBodyPairs`):
//      Closes the `bodyFields` value-spoofing seam in `branch-verifier.js` / `live-lookahead.js`
//      (where in-page JS closure drift mutates outbound values under identical JSON key names) by
//      matching the exact sorted `[flattenedPath, 64-bit digest]` multiset emitted by `branchExpression`
//      against the relational guard's attested `intentPayload`.
//   3. Cross-Step Optimistic Version Pinning (`extractRoleVersionSnapshot`):
//      Verifies that server `lockVersion` / `etag` / `modified` / `version` tokens across all
//      inspected roles remain unchanged between pre-branch Step 1 and post-branch Step 3 (`TOCTOU`
//      and `ABA` concurrent-mutation protection).
import { branchExpression, decideBranch, parseBranchResult } from '../../../src/client/branch-verifier.js';

export const PINNED_CERTIFICATE_SCHEMA = 'gammatron.pinned-relational-lookahead/v1';

const LIMIT = 64;
const TEXT = 200;
const DEPTH = 8;

export function fawnBranchDigest(value) {
  let a = 0xdeadbeef;
  let b = 0x41c6ce57;
  for (let i = 0; i < value.length; i += 1) {
    const c = value.charCodeAt(i);
    a = Math.imul(a ^ c, 2654435761);
    b = Math.imul(b ^ c, 1597334677);
  }
  a = Math.imul(a ^ (a >>> 16), 2246822507) ^ Math.imul(b ^ (b >>> 13), 3266489909);
  b = Math.imul(b ^ (b >>> 16), 2246822507) ^ Math.imul(a ^ (a >>> 13), 3266489909);
  return (b >>> 0).toString(16).padStart(8, '0') + (a >>> 0).toString(16).padStart(8, '0');
}

/**
 * Reproduces `branchExpression`'s exact JSON flattening + 64-bit digest multiset outside the browser
 * so sealed Fawn branches still export digests only while binding exact outbound values!
 */
export function computeExpectedBranchBodyPairs(intentPayload) {
  let truncated = false;
  const flatten = (value, path, out, depth) => {
    if (out.length > LIMIT) { truncated = true; return out; }
    if (value !== null && typeof value === 'object') {
      if (depth >= DEPTH) {
        truncated = true;
        out.push([path || '(body)', JSON.stringify(value)]);
        return out;
      }
      const entries = Array.isArray(value) ? value.map(item => ['[]', item]) : Object.entries(value);
      if (!entries.length) out.push([path || '(body)', JSON.stringify(value)]);
      for (const [key, item] of entries) {
        const nextPath = key === '[]' ? `${path}[]` : (path ? `${path}.${key}` : key);
        flatten(item, nextPath, out, depth + 1);
      }
      return out;
    }
    out.push([path || '(body)', JSON.stringify(value) ?? String(value)]);
    return out;
  };

  const rawEntries = flatten(intentPayload, '', [], 0);
  const fields = rawEntries.map(([name, val]) => [
    String(name).slice(0, TEXT),
    fawnBranchDigest(typeof val === 'string' ? val : (JSON.stringify(val) ?? String(val))),
  ]);
  if (fields.length > LIMIT) truncated = true;
  fields.sort((x, y) => (x[0] < y[0] ? -1 : x[0] > y[0] ? 1 : x[1] < y[1] ? -1 : x[1] > y[1] ? 1 : 0));
  return { truncated, fields: fields.slice(0, LIMIT) };
}

export function extractRoleVersionSnapshot(fetchedRows) {
  const snap = Object.create(null);
  for (const row of fetchedRows ?? []) {
    const j = row?.json?.data ?? row?.json ?? {};
    const tok = j.lockVersion ?? j.lock_version ?? j.etag ?? j.modified ?? j.updated_at ?? null;
    snap[row.sourceRole] = tok;
  }
  return snap;
}

/**
 * Coordinates pre-branch adaptive relational check, zero-egress Fawn branch preview,
 * outbound body digest pinning (`enforceBodyDigestPin`), and post-branch version-pinned re-attestation.
 */
export async function evaluatePinnedRelationalLookahead({
  adaptiveSession,
  intentPayload,
  candidates,
  fetchRole,
  runBranches,
  enforceBodyDigestPin = true,
  enforceVersionStability = true,
} = {}) {
  let totalServerReads = 0;
  const preFetchedRows = [];

  const trackedFetchPre = async role => {
    totalServerReads += 1;
    const row = await fetchRole(role, 'pre');
    preFetchedRows.push(row);
    return row;
  };

  // Step 1: Adaptive sequential server-fact guard BEFORE spawning any browser branch.
  const pre = await adaptiveSession.evaluateRoute({
    intentPayload,
    fetchRole: trackedFetchPre,
  });
  if (pre.decision !== 'eligible-for-review') {
    return Object.freeze({
      schema: PINNED_CERTIFICATE_SCHEMA,
      decision: 'abstain',
      stage: 'pre-branch-relational-guard',
      reason: pre.reason,
      winnerId: null,
      serverReads: totalServerReads,
      branchesRun: 0,
    });
  }
  const preVersions = extractRoleVersionSnapshot(preFetchedRows);

  // Step 2: Execute control + candidate actions inside sealed zero-egress Fawn branches.
  const expectedBody = computeExpectedBranchBodyPairs(intentPayload);
  if (enforceBodyDigestPin && expectedBody.truncated) {
    return Object.freeze({
      schema: PINNED_CERTIFICATE_SCHEMA,
      decision: 'abstain',
      stage: 'intent-digest-preparation',
      reason: 'expected-intent-truncated',
      winnerId: null,
      serverReads: totalServerReads,
      branchesRun: 0,
    });
  }
  const expectedFieldNames = [...new Set(expectedBody.fields.map(f => f[0]))].sort();

  const branchOutputs = await runBranches({
    controlExpression: branchExpression('0'),
    candidates: candidates.map(c => ({ id: c.id, expression: branchExpression(c.action) })),
  });
  const branchesRun = 1 + candidates.length;
  const byIdText = new Map((branchOutputs?.candidates ?? []).map(x => [x.id, x.text]));

  // Step 3: Verify Fawn branch isolation + outbound body digest pinning + post-branch server & version re-attestation.
  let postFailReason = null;
  const decided = await decideBranch({
    control: branchOutputs.control,
    candidates: candidates.map(c => ({
      id: c.id,
      text: byIdText.get(c.id),
      expect: {
        ...c.expect,
        bodyFields: c.expect?.bodyFields ?? expectedFieldNames,
      },
      fields: c.fields,
      statuses: c.statuses,
    })),
    attest: async ({ winner }) => {
      // 3a. Verify exact `[path, digest]` multiset match on the winning branch's intercepted write!
      if (enforceBodyDigestPin) {
        const parsed = parseBranchResult(byIdText.get(winner));
        const winCand = candidates.find(c => c.id === winner);
        const expAttempt = winCand?.expect?.attempt;
        const expTarget = winCand?.expect?.target;
        const matchingIntents = (parsed.result?.value?.intents ?? []).filter(
          it => it.api === expAttempt && (it.target === expTarget || it.url === expTarget),
        );
        const recordedFields = matchingIntents[0]?.body?.fields ?? null;
        if (!recordedFields || JSON.stringify(recordedFields) !== JSON.stringify(expectedBody.fields)) {
          postFailReason = 'branch-body-digest-mismatch';
          return { holds: false };
        }
      }

      // 3b. Re-verify server relational predicates AND version-token stability (`TOCTOU` / `ABA` check).
      const postFetchedRows = [];
      const post = await adaptiveSession.evaluateRoute({
        intentPayload,
        fetchRole: async role => {
          totalServerReads += 1;
          const r = await fetchRole(role, 'post');
          postFetchedRows.push(r);
          return r;
        },
      });
      if (post.decision !== 'eligible-for-review') {
        postFailReason = `post-branch-${post.reason}`;
        return { holds: false };
      }
      if (enforceVersionStability) {
        const postVersions = extractRoleVersionSnapshot(postFetchedRows);
        for (const [role, preTok] of Object.entries(preVersions)) {
          if (preTok !== null && role in postVersions && postVersions[role] !== preTok) {
            postFailReason = `concurrent-version-drift:${role}`;
            return { holds: false };
          }
        }
      }
      return { holds: true, facts: 'verified' };
    },
  });

  if (decided.decision !== 'review') {
    return Object.freeze({
      schema: PINNED_CERTIFICATE_SCHEMA,
      decision: 'abstain',
      stage: 'branch-or-post-attest',
      reason: postFailReason ?? decided.reason,
      winnerId: null,
      serverReads: totalServerReads,
      branchesRun,
    });
  }

  return Object.freeze({
    schema: PINNED_CERTIFICATE_SCHEMA,
    decision: 'certified',
    stage: 'verified',
    reason: null,
    winnerId: decided.winner,
    effectDigest: decided.effect,
    serverReads: totalServerReads,
    branchesRun,
  });
}
