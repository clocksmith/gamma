// Coordinates Gammatron's minimal server-fact guard with Fawn's zero-egress branch verifier.
// No network, browser, or write authority: Fawn owns isolated page branches, Gammatron selects
// minimal server facts and prunes candidate actions, and `reuse` / `repair` emits an inspectable
// certificate for the review inbox or authorized executor without executing a live mutation.
import { branchExpression, decideBranch } from './branch-verifier.js';
import { checkRepairBoundary, collectObservedFacts } from './repair-boundary.js';

export const CERTIFICATE_SCHEMA = 'gammatron.live-lookahead-certificate/v1';
export const MAX_LOOKAHEAD_BRANCHES = 8;

const KINDS = new Set(['reuse', 'repair']);

/**
 * Extracts the exact minimal set of non-`intent` server roles referenced by a learned guard,
 * skipping unreferenced discovery roles so runtime verification pays only minimal reads.
 */
export function extractMinimalReadRoles(boundary) {
  if (boundary?.status !== 'learned' || !Array.isArray(boundary.guard)) return Object.freeze([]);
  const roles = new Set();
  for (const term of boundary.guard) {
    for (const ref of [term?.left, term?.right]) {
      if (typeof ref !== 'string') continue;
      const cut = ref.indexOf(':');
      if (cut <= 0) continue;
      const role = ref.slice(0, cut);
      if (role !== 'intent') roles.add(role);
    }
  }
  return Object.freeze([...roles].sort());
}

const makeCertificate = fields => Object.freeze({
  schema: CERTIFICATE_SCHEMA,
  decision: 'abstain',
  stage: 'input-validation',
  reason: null,
  intendedEffect: null,
  winnerId: null,
  winnerKind: null,
  effectDigest: null,
  checkedPredicates: Object.freeze([]),
  requiredRoles: Object.freeze([]),
  serverReads: 0,
  branchesRun: 0,
  candidateVerdicts: Object.freeze([]),
  ...fields,
});

/**
 * Evaluates a stored `reuse` candidate and optional `repair` candidates against:
 *   1. Minimal authoritative server prerequisites (`checkRepairBoundary`) BEFORE branching,
 *      short-circuiting at 0 branches when server state already forbids the write;
 *   2. Zero-egress Fawn branch previews (`branchExpression` + `decideBranch`) over the top-k
 *      (`1 <= pruneTopK <= 8`) candidates compared against a no-op control branch;
 *   3. Post-branch authoritative re-attestation of the same minimal server roles.
 */
export async function evaluateLiveLookahead({
  boundary,
  intendedEffect,
  candidates,
  pruneTopK = MAX_LOOKAHEAD_BRANCHES,
  readServerRoles,
  runBranches,
} = {}) {
  if (typeof intendedEffect !== 'string' || boundary?.status !== 'learned') {
    return makeCertificate({
      reason: boundary?.reason ?? 'boundary-not-learned',
      intendedEffect: typeof intendedEffect === 'string' ? intendedEffect : null,
    });
  }
  if (!Number.isInteger(pruneTopK) || pruneTopK < 1 || pruneTopK > MAX_LOOKAHEAD_BRANCHES) {
    return makeCertificate({ reason: 'invalid-prune-budget', intendedEffect });
  }
  if (!Array.isArray(candidates) || candidates.length === 0) {
    return makeCertificate({ reason: 'invalid-candidates', intendedEffect });
  }
  if (typeof readServerRoles !== 'function' || typeof runBranches !== 'function') {
    return makeCertificate({ reason: 'missing-observer-callbacks', intendedEffect });
  }

  const pruned = candidates.slice(0, pruneTopK);
  const seenIds = new Set();
  for (const cand of pruned) {
    if (!cand || typeof cand.id !== 'string' || !cand.id || seenIds.has(cand.id) || !KINDS.has(cand.kind)
        || typeof cand.action !== 'string' || !cand.action.trim()) {
      return makeCertificate({ reason: 'invalid-candidates', intendedEffect });
    }
    seenIds.add(cand.id);
  }

  const requiredRoles = extractMinimalReadRoles(boundary);
  let serverReads = 0;

  const checkServer = async () => {
    const fetched = await readServerRoles(requiredRoles);
    const readsUsed = Number.isSafeInteger(fetched?.reads) ? fetched.reads : requiredRoles.length;
    serverReads += readsUsed;
    const observation = collectObservedFacts(fetched?.responses ?? []);
    const verdict = checkRepairBoundary(boundary, observation, intendedEffect);
    return { observation, verdict };
  };

  // Step 1: Minimal server-fact check before spawning any renderer branch.
  let pre;
  try {
    pre = await checkServer();
  } catch {
    return makeCertificate({
      stage: 'pre-branch-facts',
      reason: 'server-read-failed',
      intendedEffect,
      checkedPredicates: boundary.guard,
      requiredRoles,
      serverReads,
    });
  }
  if (pre.verdict.status !== 'eligible-for-review') {
    return makeCertificate({
      stage: 'pre-branch-facts',
      reason: pre.verdict.reason,
      intendedEffect,
      checkedPredicates: boundary.guard,
      requiredRoles,
      serverReads,
      branchesRun: 0,
    });
  }

  // Step 2: Run 1 no-op control + pruned top-k candidate expressions in zero-egress branches.
  let branchOutputs;
  try {
    branchOutputs = await runBranches({
      controlExpression: branchExpression('0'),
      candidates: pruned.map(c => ({ id: c.id, expression: branchExpression(c.action) })),
    });
  } catch {
    return makeCertificate({
      stage: 'branch-preview',
      reason: 'branch-execution-failed',
      intendedEffect,
      checkedPredicates: boundary.guard,
      requiredRoles,
      serverReads,
    });
  }

  const branchesRun = Number.isSafeInteger(branchOutputs?.branchesRun)
    ? branchOutputs.branchesRun
    : 1 + pruned.length;
  const byIdText = new Map((branchOutputs?.candidates ?? []).map(item => [item?.id, item?.text]));

  // Step 3: Verify branch observations + post-branch authoritative server re-attestation.
  let postReason = null;
  const decided = await decideBranch({
    control: branchOutputs?.control,
    candidates: pruned.map(c => ({
      id: c.id,
      text: byIdText.get(c.id),
      expect: c.expect,
      fields: c.fields,
      statuses: c.statuses,
      accepts: c.accepts,
    })),
    attest: async () => {
      const post = await checkServer();
      if (post.verdict.status !== 'eligible-for-review') {
        postReason = post.verdict.reason;
        return { holds: false };
      }
      return { holds: true, facts: post.observation.facts };
    },
  });

  const frozenVerdicts = Object.freeze((decided.rows ?? []).map(r => Object.freeze({ ...r })));
  if (decided.decision !== 'review') {
    return makeCertificate({
      stage: 'branch-or-post-attest',
      reason: postReason ?? decided.reason,
      intendedEffect,
      checkedPredicates: boundary.guard,
      requiredRoles,
      serverReads,
      branchesRun,
      candidateVerdicts: frozenVerdicts,
    });
  }

  const winnerCandidate = pruned.find(c => c.id === decided.winner);
  return makeCertificate({
    decision: winnerCandidate.kind,
    stage: 'verified',
    reason: null,
    intendedEffect,
    winnerId: decided.winner,
    winnerKind: winnerCandidate.kind,
    effectDigest: decided.effect,
    checkedPredicates: boundary.guard,
    requiredRoles,
    serverReads,
    branchesRun,
    candidateVerdicts: frozenVerdicts,
  });
}
