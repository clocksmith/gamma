// Experimental repair transfer classifier. No network or write authority.
const LIMITS = Object.freeze({
  responses: 16, facts: 96, depth: 5, size: 4096, examples: 24, candidates: 512, states: 20000,
});
const OP_BINDING = /^opbind-v1:[a-f0-9]{64}$/;
const ROLE = /^[a-z][a-z0-9_-]{0,47}$/;
const KEY = /^[A-Za-z_][A-Za-z0-9_.-]{0,63}$/;
const UNSAFE_KEY = /(?:^$|constructor|prototype|password|credential|secret|token|cookie|auth|e-?mail|phone|name|description|note|comment|content|url|uri|href|activity|journal|(?:^|[_-])id(?:$|[_-])|Id$|ID$)/i;
const DURATION = /^P(?=.{1,28}$)(?:\d{1,5}D)?(?:T(?:\d{1,5}H)?(?:\d{1,5}M)?(?:\d{1,5}S)?)?$/;
const own = (object, key) => Object.hasOwn(object, key);
const plain = value => value !== null && typeof value === 'object' &&
  [Object.prototype, null].includes(Object.getPrototypeOf(value));
const scalar = value => typeof value === 'boolean' || Number.isSafeInteger(value)
  || (typeof value === 'string' && value !== 'PT' && DURATION.test(value));
const field = key => KEY.test(key) && !UNSAFE_KEY.test(key.replace(/([a-z0-9])([A-Z])/g, '$1_$2'));
const escapePointer = segment => segment.replaceAll('~', '~0').replaceAll('/', '~1');
const validFact = key => {
  const split = key.indexOf(':');
  const role = key.slice(0, split);
  const path = key.slice(split + 1).split('/');
  return split > 0 && ROLE.test(role) && path[0] === '' && path.length > 1 &&
    path.length <= LIMITS.depth + 1 && path.slice(1).every(field);
};
const stop = reason => Object.freeze({ status: 'abstain', reason });

/**
 * The caller is the observation trust boundary: it assigns stable roles shared by
 * examples and establishes origin, provenance and freshness. Do not pass model
 * assertions, storage, arbitrary headers, or untrusted role names as observations.
 * Retains booleans, safe integers and bounded ISO duration literals only, not raw
 * URLs, free text, arrays, dates, IDs, credentials or response bodies.
 */
export function collectObservedFacts(responses) {
  if (!Array.isArray(responses) || responses.length > LIMITS.responses) return stop('catalog-budget');
  const facts = Object.create(null);
  const seen = new Set();
  let size = 0;
  let factCount = 0;
  let exhausted = false;
  const visit = (body, role, path, depth) => {
    if (exhausted || depth >= LIMITS.depth || !plain(body)) return;
    for (const key in body) {
      if (!own(body, key)) continue;
      if (++size > LIMITS.size) { exhausted = true; return; }
      if (!field(key)) continue;
      const d = Object.getOwnPropertyDescriptor(body, key);
      if (!d || !('value' in d)) continue;
      const value = d.value;
      const next = path + '/' + escapePointer(key);
      if (scalar(value)) {
        if (++factCount > LIMITS.facts) { exhausted = true; return; }
        facts[`${role}:${next}`] = value;
      } else visit(value, role, next, depth + 1);
    }
  };
  for (const row of responses) {
    if (!plain(row) || row.sameOrigin !== true || row.method !== 'GET' ||
        !['fetch', 'xhr'].includes(row.transport) || !Number.isInteger(row.status) ||
        row.status < 200 || row.status >= 300 || !ROLE.test(row.sourceRole ?? '')) continue;
    if (seen.has(row.sourceRole)) return stop('ambiguous-source-role');
    seen.add(row.sourceRole);
    visit(row.json, row.sourceRole, '', 0);
    if (exhausted) return stop('catalog-budget');
  }
  return Object.freeze({ status: 'observed', facts: Object.freeze(facts) });
}

const has = (facts, key) => own(facts, key) && scalar(facts[key]);
function evaluateTerm(term, facts) {
  if (!plain(term) || typeof term.left !== 'string' || !validFact(term.left)) return null;
  if (!has(facts, term.left)) return null;
  if (term.kind === 'equals-literal' && scalar(term.value) && typeof term.value === typeof facts[term.left]) {
    return facts[term.left] === term.value;
  }
  if (term.kind !== 'equals-field' || typeof term.right !== 'string' || !validFact(term.right) ||
      term.left === term.right || !has(facts, term.right) ||
      typeof facts[term.left] !== typeof facts[term.right]) return null;
  return facts[term.left] === facts[term.right];
}

/**
 * Exact minimum over distinct observed field reads in the bounded candidate
 * language; not a causal claim and not a bound on unseen cases. If several
 * guards are equally cheap, request another teaching example instead of
 * guessing. Only pure eligibility is returned; commit checks stay external.
 */
export function learnRepairBoundary({ positive, negative, intendedEffect } = {}) {
  if (typeof intendedEffect !== 'string' || !OP_BINDING.test(intendedEffect)) return stop('invalid-operation-reference');
  if (!Array.isArray(positive) || !Array.isArray(negative) || !positive.length ||
      !negative.length || positive.length + negative.length > LIMITS.examples) return stop('invalid-examples');
  const evidence = [...positive, ...negative];
  if (evidence.some(x => x?.status !== 'observed' || !plain(x.facts) ||
      Object.keys(x.facts).length > LIMITS.facts ||
      Object.entries(x.facts).some(([k, v]) => !validFact(k) || !scalar(v)))) return stop('unavailable-teaching-evidence');
  const positives = positive.map(x => x.facts);
  const negatives = negative.map(x => x.facts);
  const paths = Object.keys(positives[0]).sort().filter(key => positives.every(f => has(f, key)));
  const terms = [];
  const add = (term, reads) => {
    if (!positives.every(f => evaluateTerm(term, f) === true)) return;
    let cover = 0;
    negatives.forEach((f, i) => { if (evaluateTerm(term, f) === false) cover |= 1 << i; });
    if (cover) terms.push({ term, reads, cover });
  };
  for (let i = 0; i < paths.length; i++) {
    const left = paths[i];
    add({ kind: 'equals-literal', left, value: positives[0][left] }, [left]);
    for (let j = i + 1; j < paths.length; j++) {
      const right = paths[j];
      add({ kind: 'equals-field', left, right }, [left, right]);
      if (terms.length > LIMITS.candidates) return stop('search-budget');
    }
  }
  const target = (1 << negatives.length) - 1;
  if (terms.reduce((cover, term) => cover | term.cover, 0) !== target) return stop('no-separating-guard');
  const visited = new Set();
  let best = null;
  let bestCost = Infinity;
  let bestTermCount = Infinity;
  let tied = false;
  let exhausted = false;
  const visit = (mask, indices, reads) => {
    if (reads.size > bestCost || exhausted) return;
    const state = [...indices].sort((a, b) => a - b).join(',');
    if (visited.has(state)) return;
    if (visited.size >= LIMITS.states) { exhausted = true; return; }
    visited.add(state);
    if (mask === target) {
      if (reads.size < bestCost || (reads.size === bestCost && indices.length < bestTermCount)) {
        best = [...indices].sort((a, b) => a - b);
        bestCost = reads.size;
        bestTermCount = indices.length;
        tied = false;
      } else if (reads.size === bestCost && indices.length === bestTermCount) tied = true;
      return;
    }
    if (reads.size === bestCost && indices.length >= bestTermCount) return;
    const bit = (target & ~mask) & -(target & ~mask);
    for (let i = 0; i < terms.length; i++) {
      const item = terms[i];
      if (!(item.cover & bit)) continue;
      visit(mask | item.cover, [...indices, i], new Set([...reads, ...item.reads]));
    }
  };
  visit(0, [], new Set());
  if (exhausted || !best) return stop('search-budget');
  if (tied) return stop('ambiguous-minimum');
  return Object.freeze({
    status: 'learned',
    intendedEffect,
    guard: Object.freeze(best.map(i => Object.freeze(terms[i].term))),
    trainingReadCount: bestCost,
  });
}

/** The caller supplies the expected effect from its authoritative write path. */
export function checkRepairBoundary(boundary, observation, intendedEffect) {
  if (typeof intendedEffect !== 'string' || !OP_BINDING.test(intendedEffect) ||
      boundary?.status !== 'learned' || intendedEffect !== boundary.intendedEffect) return stop('operation-reference-mismatch');
  if (observation?.status !== 'observed' || !plain(observation.facts) ||
      !Array.isArray(boundary.guard) || !boundary.guard.length ||
      boundary.guard.length > LIMITS.facts) return stop('unavailable-runtime-evidence');
  const values = boundary.guard.map(term => evaluateTerm(term, observation.facts));
  if (values.includes(null)) return stop('unavailable-runtime-evidence');
  if (values.includes(false)) return stop('guard-mismatch');
  return Object.freeze({ status: 'eligible-for-review' });
}
