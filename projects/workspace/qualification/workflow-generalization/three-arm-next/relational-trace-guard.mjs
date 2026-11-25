#!/usr/bin/env node
// Zero-Adapter Typed Relational Trace Guard with 2x2 Ablation Modes (Gammatron Rung 3 Prototype).
//
// Pure, deterministic classifier with zero network, browser, or write authority.
// Addresses the two root failures of `repair-boundary.js` + hand-written per-app scalar adapters:
//   1. Zero per-app projection adapters (`adapterAuthoringMinutes = 0`, `adapterMaintenanceMinutes = 0`):
//      Extracts canonical typed facts (`bool`, `num` including fixed-point decimals, `dur`, `sym`,
//      `ref` HAL/URI links, `set` multi-value arrays, `intervals` `[start, end]` pairs, and `kmap`
//      keyed child-table maps) directly from raw HTTP GET JSON + raw `intent` write payload, while
//      hashing unprojected free-text prose (`freeTextDigest`) to abstain whenever a negative contrast
//      example differs solely in unprojected free text (`unprojected-text-hazard`).
//   2. Cross-Role Least General Generalization (`inductionMode: 'lgg-closure'` vs `'min-cover'`):
//      Retains all supported cross-role bindings (`intent <-> authority`, varying `record <-> authority`,
//      and same-leaf link/field bindings) before solving a minimal set cover for residual negatives,
//      closing the greedy minimum-cover under-constraint bug (`approval:/statusCode === 16`, NetBox 4.2
//      `scope_type` polymorphic spoof, GitLab 16.0 `approvals_required` downgrade).
import { createHash } from 'node:crypto';

const LIMITS = Object.freeze({
  responses: 16,
  facts: 160,
  depth: 6,
  size: 4096,
  examples: 32,
  candidates: 768,
  states: 25000,
});

const OP_BINDING = /^opbind-v1:[a-f0-9]{64}$/;
const ROLE = /^[a-z][a-z0-9_-]{0,47}$/;
const DURATION_PARTS = /^P(?=.{1,28}$)(?:(\d{1,5})D)?(?:T(?:(\d{1,5})H)?(?:(\d{1,5})M)?(?:(\d{1,5})S)?)?$/;
const ISO_DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/;
const ISO_DATETIME = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(?:Z|([+-]\d{2}:\d{2}))$/;
const REL_REF = /^\/[A-Za-z0-9/_.%-]{1,160}$/;
const SHORT_SYM = /^[A-Za-z0-9_.:/-]{1,48}$/;
const COMPANY_OR_LABEL = /^[A-Za-z0-9][A-Za-z0-9 _.-]{0,47}$/;

const SECRET_OR_VOLATILE_KEY = /(?:^$|constructor|prototype|password|credential|secret|access_token|refresh_token|csrf_token|api_token|bearer_token|^token$|cookie|authorization|auth_token|api_key|lock_?version|modified|created_?at|updated_?at)/i;
const FREE_TEXT_KEY = /(?:description|terms|note|notes|comment|comments|hold|embargo|raw|markdown|body_text)/i;
const RECORD_PK_KEY = /^(?:id|name|slug|url|display|doctype)$/;
const CHILD_KEY_FIELDS = ['item_code', 'sku', 'code', 'slug', 'key'];
const ADDITIVE_MAP_COLS = new Set(['qty', 'quantity', 'amount', 'hours', 'count']);
const TEMPORAL_EXPIRY_DOMAIN = new Set([
  'expires_at', 'max_expires_at', 'min_expires_at', 'not_before', 'not_after',
  'valid_from', 'valid_till', 'valid_until', 'schedule_date', 'delivery_date', 'expiry_date',
]);
const TEMPORAL_SCHEDULE_DOMAIN = new Set([
  'start_date', 'due_date', 'end_date', 'effective_date', 'target_date', 'finish_date',
  'min_start_date', 'max_due_date',
]);
const DURATION_BUDGET_DOMAIN = new Set([
  'work_duration', 'estimated_time', 'approved_duration', 'max_duration', 'min_duration', 'planned_duration',
]);

function parseDurationSeconds(str) {
  if (str === 'P' || str === 'PT') return null;
  const m = DURATION_PARTS.exec(str);
  if (!m || (!m[1] && !m[2] && !m[3] && !m[4])) return null;
  return (Number(m[1] ?? 0) * 86400)
    + (Number(m[2] ?? 0) * 3600)
    + (Number(m[3] ?? 0) * 60)
    + Number(m[4] ?? 0);
}

function tryParseIsoTimestamp(str) {
  const dm = ISO_DATE_ONLY.exec(str);
  if (dm) {
    const y = Number(dm[1]);
    const mo = Number(dm[2]);
    const d = Number(dm[3]);
    if (mo < 1 || mo > 12 || d < 1 || d > 31) return null;
    const ms = Date.UTC(y, mo - 1, d);
    const dt = new Date(ms);
    if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== mo - 1 || dt.getUTCDate() !== d) return null;
    return ms;
  }
  const tm = ISO_DATETIME.exec(str);
  if (tm) {
    const y = Number(tm[1]);
    const mo = Number(tm[2]);
    const d = Number(tm[3]);
    const hh = Number(tm[4]);
    const mm = Number(tm[5]);
    const ss = Number(tm[6]);
    if (mo < 1 || mo > 12 || d < 1 || d > 31 || hh > 23 || mm > 59 || ss > 59) return null;
    const dtCheck = new Date(Date.UTC(y, mo - 1, d));
    if (dtCheck.getUTCFullYear() !== y || dtCheck.getUTCMonth() !== mo - 1 || dtCheck.getUTCDate() !== d) return null;
    const frac = tm[7] ? `.${tm[7].slice(0, 3).padEnd(3, '0')}` : '';
    const tz = tm[8] ?? 'Z';
    const ms = Date.parse(`${tm[1]}-${tm[2]}-${tm[3]}T${tm[4]}:${tm[5]}:${tm[6]}${frac}${tz}`);
    return Number.isFinite(ms) ? ms : null;
  }
  return null;
}

const own = (obj, k) => Object.hasOwn(obj, k);
const plain = v => v !== null && typeof v === 'object' && [Object.prototype, null].includes(Object.getPrototypeOf(v));
const stop = reason => Object.freeze({ status: 'abstain', reason });
const sha256 = s => createHash('sha256').update(s, 'utf8').digest('hex');
const normNum = n => (Number.isSafeInteger(n) ? n : Math.round(n * 1e6) / 1e6);

const escapeSeg = seg => String(seg).replaceAll('~', '~0').replaceAll('/', '~1');

function isIntervalPairs(arr) {
  return Array.isArray(arr) && arr.length > 0 && arr.length <= 64 && arr.every(
    item => Array.isArray(item) && item.length === 2
      && Number.isSafeInteger(item[0]) && Number.isSafeInteger(item[1]) && item[0] <= item[1],
  );
}

function tryExtractSet(arr) {
  if (!Array.isArray(arr) || arr.length > 128) return null;
  if (arr.length === 0) return { type: 'set', elemType: 'empty', value: [] };
  if (arr.every(x => Number.isSafeInteger(x))) {
    return { type: 'set', elemType: 'num', value: [...new Set(arr)].sort((a, b) => a - b) };
  }
  if (arr.every(x => typeof x === 'string' && REL_REF.test(x))) {
    return { type: 'set', elemType: 'ref', value: [...new Set(arr)].sort() };
  }
  if (arr.every(x => typeof x === 'string' && SHORT_SYM.test(x))) {
    return { type: 'set', elemType: 'sym', value: [...new Set(arr)].sort() };
  }
  if (arr.every(x => plain(x) && typeof x.href === 'string' && REL_REF.test(x.href) && Object.keys(x).length <= 3)) {
    return { type: 'set', elemType: 'ref', value: [...new Set(arr.map(x => x.href))].sort() };
  }
  if (arr.every(x => plain(x) && Number.isSafeInteger(x.id) && Object.keys(x).length <= 3)) {
    return { type: 'set', elemType: 'num', value: [...new Set(arr.map(x => x.id))].sort((a, b) => a - b) };
  }
  return null;
}

function tryExtractKeyedChildMaps(arr) {
  if (!Array.isArray(arr) || arr.length === 0 || arr.length > 64 || !arr.every(plain)) return null;
  const keyField = CHILD_KEY_FIELDS.find(kf => arr.every(row => typeof row[kf] === 'string' && row[kf].length > 0 && row[kf].length <= 64));
  if (!keyField) return null;

  const candidateCols = Object.keys(arr[0]).filter(
    col => col !== keyField && !SECRET_OR_VOLATILE_KEY.test(col)
      && arr.every(row => typeof row[col] === 'number' && Number.isFinite(row[col])),
  );
  if (candidateCols.length === 0) return null;

  const maps = [];
  for (const col of candidateCols) {
    const byKey = new Map();
    const additive = ADDITIVE_MAP_COLS.has(col.toLowerCase());
    for (const row of arr) {
      const k = row[keyField];
      const v = normNum(row[col]);
      if (!byKey.has(k)) byKey.set(k, v);
      else byKey.set(k, additive ? normNum(byKey.get(k) + v) : Math.max(byKey.get(k), v));
    }
    const entries = [...byKey.entries()].sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
    maps.push({ keyField, col, fact: { type: 'kmap', value: entries } });
  }
  return maps;
}

/**
 * Extracts typed relational facts directly from raw GET responses + optional `intent` write body.
 * Supports `featureMode: 'typed-relational'` (default) or `'scalar-only'` (ablation).
 */
export function extractTypedTraceFacts(
  responses,
  intentPayload = null,
  { featureMode = 'typed-relational', enableTemporalOrder = true } = {},
) {
  if (!Array.isArray(responses) || responses.length > LIMITS.responses) return stop('catalog-budget');
  if (!['typed-relational', 'scalar-only'].includes(featureMode)) return stop('invalid-feature-mode');

  const relational = featureMode === 'typed-relational';
  const facts = Object.create(null);
  const freeTextChunks = [];
  const seenRoles = new Set();
  let nodes = 0;
  let factCount = 0;
  let exhausted = false;

  const putFact = (fullKey, typedVal) => {
    if (exhausted) return;
    if (++factCount > LIMITS.facts) { exhausted = true; return; }
    facts[fullKey] = typedVal;
  };

  const visit = (node, role, path, depth, leafKey = '') => {
    if (exhausted || depth > LIMITS.depth || node === null || node === undefined) return;
    if (++nodes > LIMITS.size) { exhausted = true; return; }

    if (typeof node === 'boolean') {
      putFact(`${role}:${path}`, { type: 'bool', value: node });
      return;
    }
    if (typeof node === 'number' && Number.isFinite(node)) {
      if (Number.isSafeInteger(node)) {
        // Skip record-level auto-increment primary `id` at root so learners never memorize fixture IDs,
        // while keeping foreign keys like `scope_id`, `site`, `approvals_required`, etc.
        if (depth === 1 && leafKey === 'id' && role !== 'intent') return;
        putFact(`${role}:${path}`, { type: 'num', value: node });
      } else if (relational) {
        putFact(`${role}:${path}`, { type: 'num', value: normNum(node) });
      }
      return;
    }
    if (typeof node === 'string') {
      if (FREE_TEXT_KEY.test(leafKey)) {
        if (node.trim().length > 0) freeTextChunks.push(`${role}:${path}=${node.trim()}`);
        return;
      }
      const durSec = parseDurationSeconds(node);
      if (durSec !== null) {
        putFact(`${role}:${path}`, { type: 'dur', value: node, seconds: durSec });
        return;
      }
      if (!relational) return;
      if (depth === 1 && RECORD_PK_KEY.test(leafKey) && role !== 'intent') return;
      if (enableTemporalOrder) {
        const tsMs = tryParseIsoTimestamp(node);
        if (tsMs !== null) {
          putFact(`${role}:${path}`, { type: 'ts', value: tsMs, raw: node });
          return;
        }
      }
      if (REL_REF.test(node)) {
        // Exclude self-link (`_links/self/href`) so entity URLs are never memorized.
        if (path.endsWith('/_links/self/href')) return;
        putFact(`${role}:${path}`, { type: 'ref', value: node });
        return;
      }
      if (SHORT_SYM.test(node) || (leafKey === 'company' && COMPANY_OR_LABEL.test(node))) {
        putFact(`${role}:${path}`, { type: 'sym', value: node });
        return;
      }
      if (node.trim().length > 0) freeTextChunks.push(`${role}:${path}=${node.trim()}`);
      return;
    }
    if (Array.isArray(node)) {
      if (!relational) return;
      if (isIntervalPairs(node)) {
        const sorted = [...node].map(([a, b]) => [a, b]).sort((x, y) => (x[0] - y[0]) || (x[1] - y[1]));
        putFact(`${role}:${path}`, { type: 'intervals', value: sorted });
        return;
      }
      const kmaps = tryExtractKeyedChildMaps(node);
      if (kmaps) {
        for (const m of kmaps) {
          putFact(`${role}:${path}[by=${escapeSeg(m.keyField)}]/${escapeSeg(m.col)}`, m.fact);
        }
        return;
      }
      const asSet = tryExtractSet(node);
      if (asSet && asSet.elemType !== 'empty') {
        const suffix = node[0] && plain(node[0]) && 'href' in node[0] ? '/*/href' : '';
        putFact(`${role}:${path}${suffix}`, asSet);
      }
      return;
    }
    if (plain(node)) {
      for (const k of Object.keys(node).sort()) {
        if (!own(node, k) || SECRET_OR_VOLATILE_KEY.test(k)) continue;
        visit(node[k], role, `${path}/${escapeSeg(k)}`, depth + 1, k);
        if (exhausted) return;
      }
    }
  };

  if (intentPayload !== null && intentPayload !== undefined) {
    if (!plain(intentPayload)) return stop('invalid-intent-payload');
    seenRoles.add('intent');
    visit(intentPayload, 'intent', '', 0, '');
    if (exhausted) return stop('catalog-budget');
  }

  for (const row of responses) {
    if (!plain(row) || row.sameOrigin !== true || row.method !== 'GET'
        || !['fetch', 'xhr'].includes(row.transport)
        || !Number.isInteger(row.status) || row.status < 200 || row.status >= 300
        || !ROLE.test(row.sourceRole ?? '') || row.sourceRole === 'intent') continue;
    if (seenRoles.has(row.sourceRole)) return stop('ambiguous-source-role');
    seenRoles.add(row.sourceRole);
    visit(row.json, row.sourceRole, '', 0, '');
    if (exhausted) return stop('catalog-budget');
  }

  const freeTextDigest = sha256(freeTextChunks.sort().join('\n'));
  return Object.freeze({
    status: 'observed',
    featureMode,
    facts: Object.freeze(facts),
    freeTextDigest,
    hasFreeText: freeTextChunks.length > 0,
  });
}

const roleOf = key => key.slice(0, key.indexOf(':'));
const pathOf = key => key.slice(key.indexOf(':') + 1);
const tailToken = key => {
  const parts = pathOf(key).split('/').filter(Boolean);
  if (parts.at(-1) === 'href' && parts.length >= 2) return parts.at(-2);
  return parts.at(-1) ?? '';
};
const toSnakeStem = key => tailToken(key).replace(/([a-z0-9])([A-Z])/g, '$1_$2').toLowerCase();
const stripBoundAffix = s => s.replace(/^(?:max_|min_|allowed_|approved_)/, '');

function isComparableOrderedPair(left, right, valType) {
  const sl = toSnakeStem(left);
  const sr = toSnakeStem(right);
  if (!sl || !sr) return false;
  if (stripBoundAffix(sl) === stripBoundAffix(sr)) return true;
  if (valType === 'ts') {
    return (TEMPORAL_EXPIRY_DOMAIN.has(sl) && TEMPORAL_EXPIRY_DOMAIN.has(sr))
      || (TEMPORAL_SCHEDULE_DOMAIN.has(sl) && TEMPORAL_SCHEDULE_DOMAIN.has(sr));
  }
  if (valType === 'dur') {
    return DURATION_BUDGET_DOMAIN.has(sl) && DURATION_BUDGET_DOMAIN.has(sr);
  }
  return false;
}

function factEquals(a, b) {
  if (!a || !b || a.type !== b.type) return false;
  if (a.type === 'set' && a.elemType !== b.elemType) return false;
  return JSON.stringify(a.value) === JSON.stringify(b.value);
}

export function evaluateRelationalPredicate(pred, facts) {
  const lv = facts?.[pred.left];
  if (!lv) return null;
  if (pred.kind === 'equals-literal') {
    if (lv.type !== pred.valueType) return null;
    return JSON.stringify(lv.value) === JSON.stringify(pred.value);
  }
  const rv = facts?.[pred.right];
  if (!rv) return null;
  if (pred.kind === 'equals-field') {
    if (lv.type !== rv.type) return null;
    if (lv.type === 'set' && lv.elemType !== rv.elemType) return null;
    return factEquals(lv, rv);
  }
  if (pred.kind === 'subset-of') {
    if (lv.type !== 'set' || rv.type !== 'set' || lv.elemType !== rv.elemType) return null;
    if (lv.value.length === 0) return false;
    const sup = new Set(rv.value);
    return lv.value.every(x => sup.has(x));
  }
  if (pred.kind === 'intervals-within') {
    if (lv.type !== 'intervals' || rv.type !== 'intervals') return null;
    if (lv.value.length === 0) return false;
    return lv.value.every(([a, b]) => rv.value.some(([A, B]) => A <= a && b <= B));
  }
  if (pred.kind === 'ts-lte' || pred.kind === 'ts-gte') {
    if (lv.type !== 'ts' || rv.type !== 'ts') return null;
    return pred.kind === 'ts-lte' ? lv.value <= rv.value : lv.value >= rv.value;
  }
  if (pred.kind === 'dur-lte' || pred.kind === 'dur-gte') {
    if (lv.type !== 'dur' || rv.type !== 'dur') return null;
    const ls = typeof lv.seconds === 'number' ? lv.seconds : parseDurationSeconds(lv.value);
    const rs = typeof rv.seconds === 'number' ? rv.seconds : parseDurationSeconds(rv.value);
    if (ls === null || rs === null) return null;
    return pred.kind === 'dur-lte' ? ls <= rs : ls >= rs;
  }
  if (pred.kind === 'kmap-eq' || pred.kind === 'kmap-lte') {
    if (lv.type !== 'kmap' || rv.type !== 'kmap') return null;
    if (lv.value.length === 0 || lv.value.length !== rv.value.length) return false;
    for (let i = 0; i < lv.value.length; i += 1) {
      const [lk, lnum] = lv.value[i];
      const [rk, rnum] = rv.value[i];
      if (lk !== rk) return false;
      if (pred.kind === 'kmap-eq' ? lnum !== rnum : lnum > rnum) return false;
    }
    return true;
  }
  return null;
}

function solveMinCover(candidates, targetMask) {
  if (targetMask === 0) return [];
  const unionMask = candidates.reduce((m, c) => m | (c.cover & targetMask), 0);
  if (unionMask !== targetMask) return null;
  let best = null;
  let bestReadCost = Infinity;
  let bestLen = Infinity;
  const visited = new Set();
  let states = 0;

  const search = (mask, chosenIdx, readsSet) => {
    if (readsSet.size > bestReadCost || states >= LIMITS.states) return;
    const key = [...chosenIdx].sort((a, b) => a - b).join(',');
    if (visited.has(key)) return;
    visited.add(key);
    states += 1;

    if (mask === targetMask) {
      if (readsSet.size < bestReadCost || (readsSet.size === bestReadCost && chosenIdx.length < bestLen)) {
        best = [...chosenIdx].sort((a, b) => a - b);
        bestReadCost = readsSet.size;
        bestLen = chosenIdx.length;
      }
      return;
    }
    if (readsSet.size === bestReadCost && chosenIdx.length >= bestLen) return;
    const bit = (targetMask & ~mask) & -(targetMask & ~mask);
    for (let i = 0; i < candidates.length; i += 1) {
      const effCover = candidates[i].cover & targetMask;
      if (!(effCover & bit)) continue;
      search(mask | effCover, [...chosenIdx, i], new Set([...readsSet, ...candidates[i].reads]));
    }
  };

  search(0, [], new Set());
  return best ? best.map(i => candidates[i].pred) : null;
}

/**
 * Learns a guard from positive and negative typed trace observations.
 *   - `inductionMode: 'lgg-closure'` (Cross-Role LGG Spine + Minimal Residual Negative Cover)
 *   - `inductionMode: 'min-cover'` (Ablation: greedy/exact minimum negative set cover only)
 */
export function learnRelationalTraceGuard({
  positive,
  negative,
  intendedEffect,
  inductionMode = 'lgg-closure',
} = {}) {
  if (typeof intendedEffect !== 'string' || !OP_BINDING.test(intendedEffect)) {
    return stop('invalid-operation-reference');
  }
  if (!['lgg-closure', 'min-cover'].includes(inductionMode)) return stop('invalid-induction-mode');
  if (!Array.isArray(positive) || !Array.isArray(negative) || !positive.length || !negative.length
      || positive.length + negative.length > LIMITS.examples) {
    return stop('invalid-examples');
  }
  if ([...positive, ...negative].some(x => x?.status !== 'observed' || !plain(x.facts))) {
    return stop('unavailable-teaching-evidence');
  }

  const posFacts = positive.map(x => x.facts);
  const negFacts = negative.map(x => x.facts);
  const sharedKeys = Object.keys(posFacts[0]).sort().filter(k => posFacts.every(f => own(f, k)));

  // Step 1: Contrast Indistinguishability & Unprojected Free-Text Hazard Gate.
  for (let ni = 0; ni < negFacts.length; ni += 1) {
    for (let pi = 0; pi < posFacts.length; pi += 1) {
      const sameTyped = sharedKeys.every(k => own(negFacts[ni], k) && factEquals(posFacts[pi][k], negFacts[ni][k]));
      if (sameTyped) {
        if (negative[ni].freeTextDigest !== positive[pi].freeTextDigest) {
          return stop('unprojected-text-hazard');
        }
        return stop('no-separating-guard');
      }
    }
  }

  const relational = positive[0].featureMode !== 'scalar-only';
  const allCandidates = [];
  const crossRoleLggSpine = [];

  const coverOf = pred => {
    let m = 0;
    negFacts.forEach((nf, idx) => {
      if (evaluateRelationalPredicate(pred, nf) === false) m |= (1 << idx);
    });
    return m;
  };

  const variesAcrossPositives = key => {
    const first = JSON.stringify(posFacts[0][key].value);
    return posFacts.some(pf => JSON.stringify(pf[key].value) !== first);
  };

  // Enumerate unary literals (restricted to non-`intent` scalar/ref/sym status/flag facts).
  for (const key of sharedKeys) {
    const r = roleOf(key);
    const sample = posFacts[0][key];
    if (r !== 'intent' && ['bool', 'num', 'dur', 'sym', 'ref'].includes(sample.type)) {
      if (posFacts.every(pf => factEquals(pf[key], sample))) {
        const pred = Object.freeze({
          kind: 'equals-literal',
          left: key,
          valueType: sample.type,
          value: sample.value,
        });
        const cover = coverOf(pred);
        if (cover > 0) allCandidates.push({ pred, reads: [key], cover });
      }
    }
  }

  // Enumerate cross-role binary relational predicates (`role(left) !== role(right)`).
  for (let i = 0; i < sharedKeys.length; i += 1) {
    for (let j = i + 1; j < sharedKeys.length; j += 1) {
      const a = sharedKeys[i];
      const b = sharedKeys[j];
      if (roleOf(a) === roleOf(b)) continue;
      // Canonicalize direction so `intent` or `record`/`order` appears on `left` when paired with `approval`/`quotation`.
      const rank = role => (role === 'intent' ? 0 : (role === 'record' || role === 'order' ? 1 : 2));
      const [left, right] = rank(roleOf(a)) <= rank(roleOf(b)) ? [a, b] : [b, a];
      const lv0 = posFacts[0][left];
      const rv0 = posFacts[0][right];
      if (lv0.type !== rv0.type) continue;

      const pairPreds = [];
      if (['bool', 'num', 'dur', 'ts', 'sym', 'ref', 'set', 'intervals'].includes(lv0.type)) {
        const eqPred = Object.freeze({ kind: 'equals-field', left, right });
        if (posFacts.every(pf => evaluateRelationalPredicate(eqPred, pf) === true)) {
          pairPreds.push(eqPred);
        } else if (relational && lv0.type === 'set') {
          const subPred = Object.freeze({ kind: 'subset-of', left, right });
          if (posFacts.every(pf => evaluateRelationalPredicate(subPred, pf) === true)) {
            pairPreds.push(subPred);
          }
        } else if (relational && lv0.type === 'intervals') {
          const intPred = Object.freeze({ kind: 'intervals-within', left, right });
          if (posFacts.every(pf => evaluateRelationalPredicate(intPred, pf) === true)) {
            pairPreds.push(intPred);
          }
        } else if (relational && (lv0.type === 'ts' || lv0.type === 'dur') && isComparableOrderedPair(left, right, lv0.type)) {
          const lteKind = lv0.type === 'ts' ? 'ts-lte' : 'dur-lte';
          const gteKind = lv0.type === 'ts' ? 'ts-gte' : 'dur-gte';
          const ltePred = Object.freeze({ kind: lteKind, left, right });
          const gtePred = Object.freeze({ kind: gteKind, left, right });
          if (posFacts.every(pf => evaluateRelationalPredicate(ltePred, pf) === true)) {
            pairPreds.push(ltePred);
          } else if (posFacts.every(pf => evaluateRelationalPredicate(gtePred, pf) === true)) {
            pairPreds.push(gtePred);
          }
        }
      } else if (relational && lv0.type === 'kmap' && tailToken(left) === tailToken(right)) {
        const eqMap = Object.freeze({ kind: 'kmap-eq', left, right });
        const lteMap = Object.freeze({ kind: 'kmap-lte', left, right });
        if (posFacts.every(pf => evaluateRelationalPredicate(eqMap, pf) === true)) {
          pairPreds.push(eqMap);
        } else if (posFacts.every(pf => evaluateRelationalPredicate(lteMap, pf) === true)) {
          pairPreds.push(lteMap);
        }
      }

      for (const pred of pairPreds) {
        const cover = coverOf(pred);
        if (cover > 0) {
          allCandidates.push({ pred, reads: [left, right], cover });
          if (allCandidates.length > LIMITS.candidates) return stop('search-budget');
        }
        // Cross-Role LGG Spine criterion:
        // Retain cross-role invariant if it:
        //   (a) binds an explicit write-intent field (`role(left) === 'intent'`),
        //   (b) varies non-trivially across positive examples (`variesAcrossPositives`), or
        //   (c) connects matching domain attribute names across roles (`tailToken(left) === tailToken(right)`
        //       or structured `kmap`/`set`/`intervals`).
        const isStructuredCollection = ['set', 'intervals', 'kmap'].includes(lv0.type);
        const isOrderedTemporalOrDur = ['ts-lte', 'ts-gte', 'dur-lte', 'dur-gte'].includes(pred.kind);
        const sameAttrName = tailToken(left) !== '' && tailToken(left) === tailToken(right);
        const keepOrderedInSpine = !isOrderedTemporalOrDur
          || roleOf(left) === 'intent'
          || (variesAcrossPositives(left) && variesAcrossPositives(right))
          || cover > 0;
        if (keepOrderedInSpine && (roleOf(left) === 'intent' || variesAcrossPositives(left) || variesAcrossPositives(right)
            || sameAttrName || isStructuredCollection || isOrderedTemporalOrDur)) {
          crossRoleLggSpine.push({ pred, reads: [left, right], cover });
        }
      }
    }
  }

  const fullTarget = (1 << negFacts.length) - 1;

  if (inductionMode === 'min-cover') {
    const minimal = solveMinCover(allCandidates, fullTarget);
    if (!minimal) return stop('no-separating-guard');
    const readSet = new Set(minimal.flatMap(p => (p.right ? [p.left, p.right] : [p.left])));
    return Object.freeze({
      status: 'learned',
      intendedEffect,
      inductionMode,
      featureMode: positive[0].featureMode,
      guard: Object.freeze(minimal),
      trainingReadCount: readSet.size,
    });
  }

  // `lgg-closure` mode: start from Cross-Role LGG Spine, then solve minimal cover for any uncovered negatives.
  let coveredBySpine = 0;
  for (const item of crossRoleLggSpine) coveredBySpine |= item.cover;
  const residualMask = fullTarget & ~coveredBySpine;
  const residualPreds = solveMinCover(allCandidates, residualMask);
  if (residualPreds === null) return stop('no-separating-guard');

  const seenPredJson = new Set();
  const merged = [];
  for (const p of [...crossRoleLggSpine.map(x => x.pred), ...residualPreds]) {
    const sig = JSON.stringify(p);
    if (!seenPredJson.has(sig)) {
      seenPredJson.add(sig);
      merged.push(p);
    }
  }
  const readSet = new Set(merged.flatMap(p => (p.right ? [p.left, p.right] : [p.left])));
  return Object.freeze({
    status: 'learned',
    intendedEffect,
    inductionMode,
    featureMode: positive[0].featureMode,
    guard: Object.freeze(merged),
    trainingReadCount: readSet.size,
  });
}

export function checkRelationalTraceGuard(boundary, observation, intendedEffect) {
  if (typeof intendedEffect !== 'string' || !OP_BINDING.test(intendedEffect)
      || boundary?.status !== 'learned' || boundary.intendedEffect !== intendedEffect) {
    return stop('operation-reference-mismatch');
  }
  if (observation?.status !== 'observed' || !plain(observation.facts)
      || !Array.isArray(boundary.guard) || boundary.guard.length === 0) {
    return stop('unavailable-runtime-evidence');
  }
  for (const pred of boundary.guard) {
    const res = evaluateRelationalPredicate(pred, observation.facts);
    if (res === null) return stop('unavailable-runtime-evidence');
    if (res === false) return stop('guard-mismatch');
  }
  return Object.freeze({ status: 'eligible-for-review' });
}
