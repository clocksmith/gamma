// Learned Repair-Validity Boundary (`RepairBoundary`) for `attested-modular-skill` (#88).
//
// Separates a repaired UI workflow module into four distinct, SHA-256-frozen records:
//   1. `proposedRepair`      — updated UI step sequence for the upgraded screen;
//   2. `intendedEffect`      — non-waivable server commit contract (`opbind-v1`);
//   3. `counterexamples`     — disposable near-miss records with look-alike DOMs;
//   4. `discriminatingGuard` — minimal conjunction over an auto-extracted raw GET/XHR
//                              fact catalog separating valid transfers from near misses.
//
// Safety invariants:
//   - Pre-cooked oracle keys (e.g. `repairIsValid`, `canTransfer`) are rejected at catalog extraction.
//   - If no raw fact conjunction separates positives from counterexamples, or any required fact
//     read is unavailable at runtime, `evaluateRepairBoundary` abstains (`allowReuse: false`).
//   - `intendedEffect` remains enforced at commit; the boundary proposes reuse, never waives commit checks.

import { createHash } from 'node:crypto';

const FORBIDDEN_ORACLE_KEY_RE =
  /(?:repair[_-]?is[_-]?valid|valid[_-]?for[_-]?repair|can[_-]?transfer|allow[_-]?skip[_-]?oracle|should[_-]?proceed[_-]?oracle|is[_-]?authorized[_-]?oracle)/i;

const VOLATILE_KEY_RE =
  /^(?:createdAt|updatedAt|created_at|updated_at|etag|requestId|request_id|csrfToken|csrf_token|nonce)$/i;

function canonicalJson(val) {
  if (val === null || typeof val !== 'object') return JSON.stringify(val);
  if (Array.isArray(val)) return `[${val.map(canonicalJson).join(',')}]`;
  const keys = Object.keys(val).sort();
  return `{${keys
    .filter(k => val[k] !== undefined)
    .map(k => `${JSON.stringify(k)}:${canonicalJson(val[k])}`)
    .join(',')}}`;
}

const sha256Hex = text => createHash('sha256').update(text, 'utf8').digest('hex');

function inferEndpointTag(url) {
  let pathname = String(url ?? '');
  try {
    pathname = new URL(pathname, 'http://localhost').pathname;
  } catch {
    // keep raw path
  }
  const parts = pathname
    .split('/')
    .filter(Boolean)
    .filter(seg => !/^v\d+$/i.test(seg) && seg !== 'api');
  if (parts.length === 0) return 'root';
  const last = parts[parts.length - 1];
  const prev = parts.length >= 2 ? parts[parts.length - 2] : null;
  if (/^\d+$/.test(last) && prev) {
    return prev.replace(/s$/, '');
  }
  return last;
}

function flattenJsonScalars(node, prefix, out, depth = 0, maxDepth = 5) {
  if (depth > maxDepth || node === undefined) return;
  if (node === null || typeof node === 'string' || typeof node === 'number' || typeof node === 'boolean') {
    out[prefix] = node;
    return;
  }
  if (Array.isArray(node)) {
    out[`${prefix}.length`] = node.length;
    if (node.length > 0) {
      flattenJsonScalars(node[node.length - 1], `${prefix}.latest`, out, depth + 1, maxDepth);
      // Also surface the latest status/approval-bearing element if elements carry `details` or `status`:
      for (let i = node.length - 1; i >= 0; i -= 1) {
        const el = node[i];
        const hasStatusDetail =
          Array.isArray(el?.details)
          && el.details.some(d => /status/i.test(String(d?.raw ?? '')));
        if (hasStatusDetail || el?.kind === 'approval') {
          flattenJsonScalars(el, `${prefix}.latestStatusEntry`, out, depth + 1, maxDepth);
          break;
        }
      }
    }
    return;
  }
  for (const key of Object.keys(node).sort()) {
    if (FORBIDDEN_ORACLE_KEY_RE.test(key)) {
      const err = Error(`Forbidden pre-cooked oracle key in fact catalog: ${key}`);
      err.code = 'forbidden-oracle-fact-key';
      throw err;
    }
    if (VOLATILE_KEY_RE.test(key)) continue;
    const val = node[key];
    if (key === '_embedded' && val && Array.isArray(val.elements)) {
      flattenJsonScalars(val.elements, `${prefix}.elements`, out, depth + 1, maxDepth);
      continue;
    }
    const nextPrefix = prefix ? `${prefix}.${key}` : key;
    flattenJsonScalars(val, nextPrefix, out, depth + 1, maxDepth);
  }
}

/**
 * Populate a raw server fact catalog at `$0` directly from observed read-only HTTP (`GET`)
 * JSON responses without any task-specific boolean oracle.
 */
export function extractRawFactCatalogFromHttpTrace(exchanges, { maxDepth = 5 } = {}) {
  if (!Array.isArray(exchanges)) {
    throw Error('extractRawFactCatalogFromHttpTrace requires an array of HTTP exchanges');
  }
  const facts = {};
  const unavailableTags = new Set();
  let factReadCount = 0;

  for (const ex of exchanges) {
    const method = String(ex?.method ?? 'GET').toUpperCase();
    if (method !== 'GET' && !ex?.isReadOnlyQuery) continue;
    factReadCount += 1;
    const tag = ex?.roleTag ? String(ex.roleTag) : inferEndpointTag(ex?.url);
    if (FORBIDDEN_ORACLE_KEY_RE.test(tag)) {
      const err = Error(`Forbidden pre-cooked oracle tag in fact catalog: ${tag}`);
      err.code = 'forbidden-oracle-fact-key';
      throw err;
    }
    const status = Number(ex?.status ?? 0);
    if (ex?.unavailable === true || status < 200 || status >= 300 || ex?.body === undefined || ex?.body === null) {
      unavailableTags.add(tag);
      continue;
    }
    flattenJsonScalars(ex.body, tag, facts, 0, maxDepth);
  }

  return {
    facts,
    unavailableTags: [...unavailableTags].sort(),
    factReadCount,
  };
}

function topPrefix(path) {
  const idx = path.indexOf('.');
  return idx === -1 ? path : path.slice(0, idx);
}

function clausePriorityScore(clause) {
  // Prefer relational cross-entity/cross-journal invariants (`eq_path`) over literal constants
  // (`eq_literal`) so guards generalize to unseen records with new parameter values (e.g. `PT16H`).
  let score = clause.kind === 'eq_path' ? 0 : 10;
  const pathStr = clause.kind === 'eq_path' ? `${clause.leftPath}|${clause.rightPath}` : clause.path;
  if (/(?:status|lockVersion|version|estimatedTime|terms|approved|role)/i.test(pathStr)) {
    score -= 3;
  }
  if (/\.id$/i.test(pathStr) || /\.subject$/i.test(pathStr)) {
    score += 5;
  }
  return score;
}

export function evaluateGuardClause(clause, facts) {
  if (clause.kind === 'eq_literal') {
    if (!(clause.path in facts)) return { status: 'unavailable', missingPath: clause.path };
    return { status: facts[clause.path] === clause.expected ? 'true' : 'false' };
  }
  if (clause.kind === 'eq_path') {
    if (!(clause.leftPath in facts)) return { status: 'unavailable', missingPath: clause.leftPath };
    if (!(clause.rightPath in facts)) return { status: 'unavailable', missingPath: clause.rightPath };
    return { status: facts[clause.leftPath] === facts[clause.rightPath] ? 'true' : 'false' };
  }
  throw Error(`Unsupported guard clause kind: ${clause.kind}`);
}

/**
 * Synthesize the minimal conjunction of raw catalog clauses that holds on every positive
 * repair snapshot and is refuted on every disposable near-miss counterexample snapshot.
 */
export function synthesizeDiscriminatingGuard({
  positiveSnapshots,
  counterexampleSnapshots,
  maxConjunctionArity = 2,
}) {
  if (!Array.isArray(positiveSnapshots) || positiveSnapshots.length === 0) {
    throw Error('synthesizeDiscriminatingGuard requires at least 1 positive snapshot');
  }
  if (!Array.isArray(counterexampleSnapshots) || counterexampleSnapshots.length === 0) {
    return {
      status: 'unseparated',
      reason: 'no-counterexamples-supplied',
      clauses: [],
      requiredPaths: [],
    };
  }

  const firstPos = positiveSnapshots[0];
  const sharedPaths = Object.keys(firstPos)
    .filter(p => !/\.id$/i.test(p) && positiveSnapshots.every(s => p in s))
    .sort();

  const candidates = [];

  // 1. Relational cross-subtree equality candidates (`fact[leftPath] === fact[rightPath]`):
  for (let i = 0; i < sharedPaths.length; i += 1) {
    for (let j = i + 1; j < sharedPaths.length; j += 1) {
      const lp = sharedPaths[i];
      const rp = sharedPaths[j];
      if (topPrefix(lp) === topPrefix(rp)) continue;
      if (typeof firstPos[lp] !== typeof firstPos[rp] || firstPos[lp] === null) continue;
      const holdsAllPos = positiveSnapshots.every(s => s[lp] === s[rp]);
      if (!holdsAllPos) continue;
      const refutesAnyNeg = counterexampleSnapshots.some(
        n => lp in n && rp in n && n[lp] !== n[rp],
      );
      if (refutesAnyNeg) {
        candidates.push({ kind: 'eq_path', leftPath: lp, rightPath: rp });
      }
    }
  }

  // 2. Literal invariant candidates (`fact[path] === val`):
  for (const path of sharedPaths) {
    const val = firstPos[path];
    if (positiveSnapshots.every(s => s[path] === val)) {
      const refutesAnyNeg = counterexampleSnapshots.some(n => path in n && n[path] !== val);
      if (refutesAnyNeg) {
        candidates.push({ kind: 'eq_literal', path, expected: val });
      }
    }
  }

  candidates.sort((a, b) => {
    const diff = clausePriorityScore(a) - clausePriorityScore(b);
    if (diff !== 0) return diff;
    return canonicalJson(a).localeCompare(canonicalJson(b));
  });

  const separatesAllNegs = clauseList =>
    counterexampleSnapshots.every(neg =>
      clauseList.some(c => evaluateGuardClause(c, neg).status === 'false'),
    );

  const collectPaths = clauseList => {
    const s = new Set();
    for (const c of clauseList) {
      if (c.kind === 'eq_literal') s.add(c.path);
      else {
        s.add(c.leftPath);
        s.add(c.rightPath);
      }
    }
    return [...s].sort();
  };

  // Arity 1 search (single minimal discriminating read):
  for (const c1 of candidates) {
    if (separatesAllNegs([c1])) {
      return {
        status: 'separated',
        arity: 1,
        clauses: [c1],
        requiredPaths: collectPaths([c1]),
      };
    }
  }

  // Arity 2 search (minimal pair conjunction):
  if (maxConjunctionArity >= 2) {
    for (let i = 0; i < candidates.length; i += 1) {
      for (let j = i + 1; j < candidates.length; j += 1) {
        const pair = [candidates[i], candidates[j]];
        if (separatesAllNegs(pair)) {
          return {
            status: 'separated',
            arity: 2,
            clauses: pair,
            requiredPaths: collectPaths(pair),
          };
        }
      }
    }
  }

  return {
    status: 'unseparated',
    reason: 'no-discriminating-conjunction-in-catalog',
    clauses: [],
    requiredPaths: [],
  };
}

function computeBoundaryDigest(payloadWithoutDigest) {
  return sha256Hex(canonicalJson(payloadWithoutDigest));
}

/**
 * Construct and SHA-256-freeze a `RepairBoundary` separating `proposedRepair`,
 * `intendedEffect`, `counterexamples`, and `discriminatingGuard`.
 */
export function createAndFreezeRepairBoundary({
  moduleId,
  proposedRepair,
  intendedEffect,
  positiveTraces,
  counterexampleTraces,
  maxConjunctionArity = 2,
}) {
  if (!moduleId || typeof moduleId !== 'string') {
    throw Error('createAndFreezeRepairBoundary requires moduleId');
  }
  if (!proposedRepair || typeof proposedRepair !== 'object' || !Array.isArray(proposedRepair.steps)) {
    throw Error('createAndFreezeRepairBoundary requires proposedRepair.steps');
  }
  if (
    !intendedEffect
    || typeof intendedEffect !== 'object'
    || intendedEffect.operationBindingSchema !== 'opbind-v1'
    || intendedEffect.nonWaivableByModel !== true
  ) {
    throw Error(
      'createAndFreezeRepairBoundary requires intendedEffect with operationBindingSchema="opbind-v1" and nonWaivableByModel=true',
    );
  }

  const posCatalogs = positiveTraces.map(t =>
    t.facts ? { facts: t.facts, unavailableTags: [] } : extractRawFactCatalogFromHttpTrace(t.httpExchanges),
  );
  const negCatalogs = counterexampleTraces.map(t =>
    t.facts ? { facts: t.facts, unavailableTags: [] } : extractRawFactCatalogFromHttpTrace(t.httpExchanges),
  );

  const discriminatingGuard = synthesizeDiscriminatingGuard({
    positiveSnapshots: posCatalogs.map(c => c.facts),
    counterexampleSnapshots: negCatalogs.map(c => c.facts),
    maxConjunctionArity,
  });

  const core = {
    schema: 'gammatron.repair-boundary/v1',
    moduleId,
    learnRepairs: false,
    proposedRepair: structuredClone(proposedRepair),
    intendedEffect: structuredClone(intendedEffect),
    counterexamples: counterexampleTraces.map((t, idx) => ({
      id: t.id ?? `counterexample-${idx + 1}`,
      routeId: t.routeId ?? null,
      failureKind: t.failureKind ?? 'commit-or-verifier-refuted',
      facts: negCatalogs[idx].facts,
    })),
    discriminatingGuard,
  };
  const sha256 = computeBoundaryDigest(core);
  return Object.freeze({
    ...core,
    sha256,
  });
}

/**
 * Evaluate a frozen `RepairBoundary` against an unseen route's live GET/XHR exchanges.
 * Never waives `intendedEffect`; abstains on unseparated boundaries or unavailable fact reads.
 */
export function evaluateRepairBoundary(boundary, liveHttpExchanges) {
  if (!boundary || boundary.schema !== 'gammatron.repair-boundary/v1' || !boundary.sha256) {
    const err = Error('Refusing unsealed or malformed RepairBoundary');
    err.code = 'unsealed-repair-boundary';
    throw err;
  }
  const { sha256, ...core } = boundary;
  if (computeBoundaryDigest(core) !== sha256) {
    const err = Error('RepairBoundary SHA-256 integrity check failed');
    err.code = 'tampered-repair-boundary';
    throw err;
  }

  if (boundary.discriminatingGuard.status !== 'separated') {
    return {
      decision: 'abstain',
      allowReuse: false,
      reason: boundary.discriminatingGuard.reason ?? 'unseparated-boundary',
      factReads: 0,
      failedClauses: [],
      unavailablePaths: [],
      commitContract: boundary.intendedEffect,
    };
  }

  const catalog = Array.isArray(liveHttpExchanges)
    ? extractRawFactCatalogFromHttpTrace(liveHttpExchanges)
    : {
        facts: liveHttpExchanges?.facts ?? {},
        unavailableTags: liveHttpExchanges?.unavailableTags ?? [],
        factReadCount: liveHttpExchanges?.factReadCount ?? 1,
      };

  const unavailablePaths = [];
  const failedClauses = [];
  for (const clause of boundary.discriminatingGuard.clauses) {
    const requiredForClause =
      clause.kind === 'eq_literal' ? [clause.path] : [clause.leftPath, clause.rightPath];
    if (requiredForClause.some(p => catalog.unavailableTags.includes(topPrefix(p)))) {
      unavailablePaths.push(...requiredForClause);
      continue;
    }
    const res = evaluateGuardClause(clause, catalog.facts);
    if (res.status === 'unavailable') {
      unavailablePaths.push(res.missingPath);
    } else if (res.status === 'false') {
      failedClauses.push(clause);
    }
  }

  if (unavailablePaths.length > 0) {
    return {
      decision: 'abstain',
      allowReuse: false,
      reason: 'required-fact-unavailable',
      factReads: catalog.factReadCount,
      failedClauses,
      unavailablePaths: [...new Set(unavailablePaths)].sort(),
      commitContract: boundary.intendedEffect,
    };
  }

  if (failedClauses.length > 0) {
    return {
      decision: 'refuse_transfer',
      allowReuse: false,
      reason: 'discriminating-guard-refuted',
      factReads: catalog.factReadCount,
      failedClauses,
      unavailablePaths: [],
      commitContract: boundary.intendedEffect,
    };
  }

  return {
    decision: 'reuse_repair',
    allowReuse: true,
    reason: 'discriminating-guard-satisfied',
    factReads: catalog.factReadCount,
    failedClauses: [],
    unavailablePaths: [],
    commitContract: boundary.intendedEffect,
  };
}

/**
 * Evaluate the 5-arm selective-reuse comparison on unseen routes under matched server commit rules:
 *   1. `conventional-page-object-script`
 *   2. `always-replan`
 *   3. `unguarded-shared-repair`
 *   4. `hand-written-guard`
 *   5. `learned-selective-reuse` (`RepairBoundary`)
 */
export function compareSelectiveRepairBaselines({
  boundary,
  handWrittenGuard,
  handWrittenGuardLoc = 0,
  scriptMaintainedLoc = 0,
  unseenRoutes,
  replanTurnsPerRoute = 4,
  costPerPlannerTurnUsd = 0.015,
}) {
  const arms = [
    'conventional-page-object-script',
    'always-replan',
    'unguarded-shared-repair',
    'hand-written-guard',
    'learned-selective-reuse',
  ];

  return arms.map(arm => {
    let validTransfersZeroTurns = 0;
    let legitimateRoutesNeedlesslyBlocked = 0;
    let wrongTransfersAttempted = 0;
    let wrongCommitsApplied = 0;
    let abstainedCleanly = 0;
    let plannerTurns = 0;
    let factReads = 0;

    for (const route of unseenRoutes) {
      let attemptTransfer = false;
      let usedTurns = 0;
      let reads = 0;
      let abstained = false;

      if (arm === 'conventional-page-object-script') {
        // Unchecked script replays repaired selectors blindly without reading prerequisite state:
        attemptTransfer = true;
      } else if (arm === 'always-replan') {
        const cat = extractRawFactCatalogFromHttpTrace(route.httpExchanges);
        reads = cat.factReadCount;
        usedTurns = replanTurnsPerRoute;
        attemptTransfer = route.validToTransfer === true && cat.unavailableTags.length === 0;
        if (cat.unavailableTags.length > 0) abstained = true;
      } else if (arm === 'unguarded-shared-repair') {
        attemptTransfer = true;
      } else if (arm === 'hand-written-guard') {
        const cat = extractRawFactCatalogFromHttpTrace(route.httpExchanges);
        reads = cat.factReadCount;
        const hw = handWrittenGuard(cat);
        if (hw.decision === 'abstain') abstained = true;
        else attemptTransfer = hw.allowReuse === true;
      } else if (arm === 'learned-selective-reuse') {
        const ev = evaluateRepairBoundary(boundary, route.httpExchanges);
        reads = ev.factReads;
        if (ev.decision === 'abstain') abstained = true;
        else attemptTransfer = ev.allowReuse === true;
      }

      plannerTurns += usedTurns;
      factReads += reads;
      if (abstained) abstainedCleanly += 1;

      if (attemptTransfer) {
        if (route.validToTransfer) {
          if (usedTurns === 0) validTransfersZeroTurns += 1;
        } else {
          wrongTransfersAttempted += 1;
          if (!route.serverRejectsAtCommit) {
            wrongCommitsApplied += 1;
          }
        }
      } else if (route.validToTransfer && !route.expectsAbstain) {
        legitimateRoutesNeedlesslyBlocked += 1;
      }
    }

    const guardLoc =
      arm === 'hand-written-guard'
        ? handWrittenGuardLoc
        : arm === 'conventional-page-object-script'
          ? scriptMaintainedLoc
          : 0;

    return {
      arm,
      routesEvaluated: unseenRoutes.length,
      validTransfersZeroTurns,
      legitimateRoutesNeedlesslyBlocked,
      wrongTransfersAttempted,
      wrongCommitsApplied,
      abstainedCleanly,
      plannerTurns,
      factReads,
      guardLoc,
      totalCostUsd: Number((plannerTurns * costPerPlannerTurnUsd).toFixed(6)),
    };
  });
}
