#!/usr/bin/env node
// Adaptive Sequential Role Selection & Anti-Poisoning Online Refinement for Relational Trace Guards.
//
// Pure, deterministic state machine with zero network, browser, or write authority.
// Extends `relational-trace-guard.mjs` with two Rung 3 mechanisms:
//   1. Adaptive Sequential Role Ordering (`evaluateGuardSequentially`):
//      Ranks required server roles by empirical rejection rate per GET read so high-selectivity
//      authority roles are fetched first; evaluates every predicate whose role dependencies are
//      satisfied after each GET, short-circuiting remaining server GETs and Fawn browser branches
//      immediately upon the first violated predicate.
//   2. Guarded Online Coincidence Refinement (`createAdaptiveRelationalSession`):
//      Separates immutable negative-covering predicates (`cover > 0`) from zero-variance positive
//      coincidences (`cover === 0` and zero variance across initial positive examples).
//      - When an abstention is blocked by the fallback oracle (`fallbackDecision === 'stop'`),
//        locks any separating predicate permanently (`immutable`).
//      - When an abstention is safely committed by the fallback + review oracle
//        (`fallbackDecision === 'write'`), increments a distinct-case confirmation counter on the
//        violated zero-variance predicate(s) and relaxes a spurious coincidence ONLY after
//        `kConfirm` (default `2`) independent confirmations—preventing single-fault noisy fallback
//        hallucinations from poisoning the guard while bounding false-abstention fallback cost to O(1).
import { createHash } from 'node:crypto';
import {
  evaluateRelationalPredicate,
  extractTypedTraceFacts,
  learnRelationalTraceGuard,
} from './relational-trace-guard.mjs';

const sha256 = s => createHash('sha256').update(s, 'utf8').digest('hex');
const roleOf = key => key.slice(0, key.indexOf(':'));

function requiredRolesForPredicate(pred) {
  const roles = new Set();
  if (pred.left) {
    const rl = roleOf(pred.left);
    if (rl !== 'intent') roles.add(rl);
  }
  if (pred.right) {
    const rr = roleOf(pred.right);
    if (rr !== 'intent') roles.add(rr);
  }
  return [...roles].sort();
}

function predSig(pred) {
  return JSON.stringify(pred);
}

/**
 * Inspect which predicates in `boundary.guard` separate at least one negative example (`locked`)
 * versus predicates that had zero negative cover AND zero value variance across initial positives
 * (`mutableZeroVariance`).
 */
export function classifyPredicateMutability(boundary, positiveObs, negativeObs) {
  if (boundary?.status !== 'learned') {
    return { lockedSigs: new Set(), mutableZeroVarSigs: new Set() };
  }
  const posFacts = positiveObs.map(x => x.facts);
  const negFacts = negativeObs.map(x => x.facts);

  const variesInPos = key => {
    if (!key || !posFacts.length || !(key in posFacts[0])) return false;
    const first = JSON.stringify(posFacts[0][key].value);
    return posFacts.some(pf => JSON.stringify(pf[key]?.value) !== first);
  };

  const lockedSigs = new Set();
  const mutableZeroVarSigs = new Set();

  for (const pred of boundary.guard) {
    const sig = predSig(pred);
    const coversAnyNeg = negFacts.some(nf => evaluateRelationalPredicate(pred, nf) === false);
    // Any predicate binding `intent` directly or varying across positives or covering a negative is locked!
    const bindsIntent = roleOf(pred.left) === 'intent' || (pred.right ? roleOf(pred.right) === 'intent' : false);
    const varies = variesInPos(pred.left) || (pred.right ? variesInPos(pred.right) : false);
    if (coversAnyNeg || bindsIntent || varies || pred.kind === 'equals-literal') {
      lockedSigs.add(sig);
    } else {
      mutableZeroVarSigs.add(sig);
    }
  }
  return { lockedSigs, mutableZeroVarSigs };
}

/**
 * Stateful adaptive guard session for one workflow family.
 */
export function createAdaptiveRelationalSession({
  intendedEffect,
  positiveObservations,
  negativeObservations,
  kConfirm = 2,
  enableSequentialShortCircuit = true,
  enableOnlineRefinement = true,
} = {}) {
  if (!Number.isInteger(kConfirm) || kConfirm < 1) {
    throw Error(`kConfirm must be an integer >= 1 (got ${kConfirm})`);
  }

  const initialBoundary = learnRelationalTraceGuard({
    positive: positiveObservations,
    negative: negativeObservations,
    intendedEffect,
    inductionMode: 'lgg-closure',
  });

  const { lockedSigs, mutableZeroVarSigs } = classifyPredicateMutability(
    initialBoundary,
    positiveObservations,
    negativeObservations,
  );

  let activePredicates = initialBoundary.status === 'learned' ? [...initialBoundary.guard] : [];
  const rejectCountsByRole = new Map();
  const evalCountsByRole = new Map();
  const confirmDigestsByPred = new Map();
  let refinementsApplied = 0;
  let locksPromoted = 0;

  const getOrderedRoles = () => {
    const roleSet = new Set();
    for (const p of activePredicates) {
      for (const r of requiredRolesForPredicate(p)) roleSet.add(r);
    }
    const roles = [...roleSet].sort();
    if (!enableSequentialShortCircuit) return roles;
    // Order roles by empirical Laplace-smoothed rejection rate `(rejects + 1) / (evals + 2)` descending,
    // breaking ties by putting authority roles (`approval`, `quotation`, `policy`) ahead of target `record`/`order`
    // when directly addressable so server-level unapproved states short-circuit in 1 GET!
    const authPriority = r => (['approval', 'quotation', 'policy'].includes(r) ? 0 : 1);
    return roles.sort((a, b) => {
      const scoreA = ((rejectCountsByRole.get(a) ?? 0) + 1) / ((evalCountsByRole.get(a) ?? 0) + 2);
      const scoreB = ((rejectCountsByRole.get(b) ?? 0) + 1) / ((evalCountsByRole.get(b) ?? 0) + 2);
      if (Math.abs(scoreB - scoreA) > 1e-9) return scoreB - scoreA;
      if (authPriority(a) !== authPriority(b)) return authPriority(a) - authPriority(b);
      return a < b ? -1 : a > b ? 1 : 0;
    });
  };

  /**
   * Evaluates a route by fetching server roles sequentially (if `enableSequentialShortCircuit`)
   * or in a single batch (ablation), stopping on the first violated predicate.
   *
   * `fetchRole(role)` returns `{ sameOrigin: true, method: 'GET', transport: 'fetch', status: 200, sourceRole: role, json }`.
   */
  async function evaluateRoute({ intentPayload, fetchRole }) {
    if (initialBoundary.status !== 'learned' || activePredicates.length === 0) {
      return {
        decision: 'abstain',
        reason: initialBoundary.reason ?? 'no-active-guard',
        serverReads: 0,
        fawnBranchesSpawned: 0,
        violatedPredicates: [],
        fullObservation: null,
      };
    }

    const orderedRoles = getOrderedRoles();
    const fetchedRows = [];
    const fetchedSet = new Set();
    let serverReads = 0;

    if (!enableSequentialShortCircuit) {
      for (const r of orderedRoles) {
        fetchedRows.push(await fetchRole(r));
        fetchedSet.add(r);
        serverReads += 1;
      }
      const obs = extractTypedTraceFacts(fetchedRows, intentPayload);
      const violated = activePredicates.filter(p => evaluateRelationalPredicate(p, obs.facts) !== true);
      if (violated.length > 0) {
        return {
          decision: 'abstain',
          reason: 'guard-mismatch',
          serverReads,
          fawnBranchesSpawned: 0,
          violatedPredicates: violated,
          fullObservation: obs,
        };
      }
      return {
        decision: 'eligible-for-review',
        reason: null,
        serverReads,
        fawnBranchesSpawned: 2, // 1 control + 1 pruned candidate branch in Fawn lookahead
        violatedPredicates: [],
        fullObservation: obs,
      };
    }

    // Sequential adaptive role fetching: after each GET, evaluate newly ready predicates and short-circuit!
    const checkedSigs = new Set();
    for (const r of orderedRoles) {
      fetchedRows.push(await fetchRole(r));
      fetchedSet.add(r);
      serverReads += 1;
      evalCountsByRole.set(r, (evalCountsByRole.get(r) ?? 0) + 1);

      const partialObs = extractTypedTraceFacts(fetchedRows, intentPayload);
      const readyPreds = activePredicates.filter(p => {
        const sig = predSig(p);
        if (checkedSigs.has(sig)) return false;
        return requiredRolesForPredicate(p).every(req => fetchedSet.has(req));
      });

      const failedHere = [];
      for (const p of readyPreds) {
        checkedSigs.add(predSig(p));
        if (evaluateRelationalPredicate(p, partialObs.facts) !== true) {
          failedHere.push(p);
        }
      }
      if (failedHere.length > 0) {
        rejectCountsByRole.set(r, (rejectCountsByRole.get(r) ?? 0) + 1);
        return {
          decision: 'abstain',
          reason: 'guard-mismatch',
          serverReads,
          fawnBranchesSpawned: 0,
          violatedPredicates: failedHere,
          partialFetchedRows: fetchedRows,
        };
      }
    }

    const fullObs = extractTypedTraceFacts(fetchedRows, intentPayload);
    return {
      decision: 'eligible-for-review',
      reason: null,
      serverReads,
      fawnBranchesSpawned: 2,
      violatedPredicates: [],
      fullObservation: fullObs,
    };
  }

  /**
   * Observes the authoritative outcome of a fallback invocation (`always-replan` + review check)
   * on an abstained route to either lock true separating predicates or relax `kConfirm`-verified
   * zero-variance incidental coincidences.
   */
  function recordFallbackOutcome({ fallbackDecision, fullObservation }) {
    if (!enableOnlineRefinement || initialBoundary.status !== 'learned' || !fullObservation) {
      return { action: 'noop' };
    }
    const violatedAll = activePredicates.filter(
      p => evaluateRelationalPredicate(p, fullObservation.facts) !== true,
    );
    if (violatedAll.length === 0) return { action: 'noop' };

    if (fallbackDecision === 'stop') {
      // Fallback confirmed the route is invalid: promote any mutable predicate that uniquely caught it to locked!
      let newlyLocked = 0;
      for (const p of violatedAll) {
        const sig = predSig(p);
        if (mutableZeroVarSigs.has(sig)) {
          mutableZeroVarSigs.delete(sig);
          lockedSigs.add(sig);
          newlyLocked += 1;
          locksPromoted += 1;
        }
      }
      return { action: 'locked-on-negative', newlyLocked };
    }

    if (fallbackDecision === 'write') {
      // Safety invariant: if ANY locked predicate failed, NEVER relax anything (guards against noisy fallback!).
      if (violatedAll.some(p => lockedSigs.has(predSig(p)))) {
        return { action: 'rejected-locked-violation' };
      }
      const obsDigest = sha256(JSON.stringify(fullObservation.facts));
      const dropped = [];
      for (const p of violatedAll) {
        const sig = predSig(p);
        if (!mutableZeroVarSigs.has(sig)) continue;
        if (!confirmDigestsByPred.has(sig)) confirmDigestsByPred.set(sig, new Set());
        const seen = confirmDigestsByPred.get(sig);
        seen.add(obsDigest);
        if (seen.size >= kConfirm) {
          activePredicates = activePredicates.filter(cur => predSig(cur) !== sig);
          mutableZeroVarSigs.delete(sig);
          refinementsApplied += 1;
          dropped.push(p);
        }
      }
      return { action: dropped.length > 0 ? 'relaxed-coincidence' : 'recorded-confirmation', dropped };
    }
    return { action: 'noop' };
  }

  return {
    getStatus: () => initialBoundary.status,
    getActivePredicates: () => [...activePredicates],
    getStats: () => ({
      activePredicateCount: activePredicates.length,
      lockedPredicateCount: lockedSigs.size,
      mutableZeroVarCount: mutableZeroVarSigs.size,
      refinementsApplied,
      locksPromoted,
    }),
    evaluateRoute,
    recordFallbackOutcome,
  };
}
