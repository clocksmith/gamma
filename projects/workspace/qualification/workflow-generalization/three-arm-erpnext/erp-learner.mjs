// The repair-boundary arm on ERPNext (clocksmith/deco#88). DRAFT, outside the
// frozen runner hash. As on OpenProject, the model chooses up to three reads and
// labels records it built, and `learnRepairBoundary`, unchanged, derives the guard.
//
// Supplied by the builder, as on OpenProject: `projectFrappeResourceScalars`, the
// hand-written ERPNext adapter from Gate 4. It passes on a document's status as a
// number (0 draft, 1 submitted, 2 cancelled), its total quantity, its company as
// a number and its line count, and nothing else. Its authoring cost is not measured.
// There is no fact for the write itself: the reference the write adds is free text.
import { createHash } from 'node:crypto';
import { checkRepairBoundary, collectObservedFacts, learnRepairBoundary } from '../../../src/client/repair-boundary.js';
import { projectFrappeResourceScalars } from '../repair-boundary-qualification.mjs';

export const MAX_READS = 3;
export const MAX_EXAMPLES = 24;
const ROLE = /^[a-z][a-z0-9_-]{0,47}$/;
const DOCTYPE = /^[A-Za-z][A-Za-z ]{0,63}$/;
const FIELD = /^[A-Za-z_][A-Za-z0-9_]*(?:\.(?:\d{1,2}|[A-Za-z_][A-Za-z0-9_]*)){0,4}$/;
const sha256 = text => createHash('sha256').update(text, 'utf8').digest('hex');
const canonical = value => JSON.stringify(value, (_, v) => (v && typeof v === 'object' && !Array.isArray(v)
  ? Object.fromEntries(Object.keys(v).sort().map(k => [k, v[k]])) : v));
const documentPath = (doctype, name) => `/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`;

export const intendedEffect = familyId => `opbind-v1:${sha256(canonical({
  schema: 'three-arm-operation/v1', application: 'erpnext', operation: 'add-confirmation-reference', familyId,
}))}`;

/**
 * Up to three reads. Each has a role and either `target: true` (the order the
 * write is aimed at) or `follow`: { role, field, doctype }, which reads the
 * document of that type named in a field of an earlier read, for example the
 * supplier quotation named in items.0.supplier_quotation of the order.
 */
export function validateReadPlan(plan) {
  if (!Array.isArray(plan) || !plan.length || plan.length > MAX_READS) return [`a read plan holds 1 to ${MAX_READS} reads`];
  const problems = [];
  const roles = new Set();
  plan.forEach((read, index) => {
    const at = `reads[${index}]`;
    if (!read || typeof read !== 'object') return problems.push(`${at} is not an object`);
    if (typeof read.role !== 'string' || !ROLE.test(read.role)) problems.push(`${at}.role must be a short lower-case name`);
    if (roles.has(read.role)) problems.push(`${at}.role is used twice`);
    const follows = read.follow && typeof read.follow === 'object';
    if ((read.target === true) === Boolean(follows)) problems.push(`${at} needs exactly one of target: true or follow`);
    if (follows && (!roles.has(read.follow.role) || typeof read.follow.field !== 'string' || !FIELD.test(read.follow.field)
        || typeof read.follow.doctype !== 'string' || !DOCTYPE.test(read.follow.doctype))) {
      problems.push(`${at}.follow must name an earlier role, a field of it and a document type`);
    }
    roles.add(read.role);
  });
  return problems;
}

const pick = (value, path) => path.split('.').reduce((v, key) => (v == null ? undefined : v[key]), value);

export async function observe({ plan, route, get }) {
  const bodies = new Map();
  const responses = [];
  let reads = 0;
  for (const read of plan) {
    let path = null;
    if (read.target === true) path = documentPath(route.doctype ?? 'Purchase Order', route.name);
    else {
      const named = pick(bodies.get(read.follow.role)?.data, read.follow.field);
      if (typeof named === 'string' && named && named.length <= 140) path = documentPath(read.follow.doctype, named);
    }
    if (!path) continue;
    reads += 1;
    const result = await get(path);
    if (!result?.ok || result.status < 200 || result.status >= 300 || !result.body || typeof result.body !== 'object') continue;
    bodies.set(read.role, result.body);
    responses.push({ sameOrigin: true, method: 'GET', transport: 'fetch', status: result.status, sourceRole: read.role,
      json: projectFrappeResourceScalars(result.body) });
  }
  return { observation: collectObservedFacts(responses), reads, rolesRead: [...bodies.keys()] };
}

export function createTeacher(familyIds, restore = null) {
  const families = new Map(familyIds.map(id => {
    const kept = restore?.families?.[id];
    return [id, kept ? structuredClone({ plan: kept.plan, positive: kept.positive ?? [], negative: kept.negative ?? [],
      boundary: kept.boundary?.status === 'learned' ? kept.boundary : null }) : { plan: null, positive: [], negative: [], boundary: null }];
  }));
  const family = id => { if (!families.has(id)) throw Error(`unknown family ${String(id).slice(0, 64)}`); return families.get(id); };
  return {
    setReadPlan(familyId, plan) {
      const problems = validateReadPlan(plan);
      if (problems.length) return { ok: false, problems };
      Object.assign(family(familyId), { plan: structuredClone(plan), positive: [], negative: [], boundary: null });
      return { ok: true, note: 'examples for this family were cleared' };
    },
    async addExample(familyId, label, route, get) {
      const f = family(familyId);
      if (!f.plan) return { ok: false, problems: ['set a read plan for this family first'] };
      if (!['valid', 'invalid'].includes(label)) return { ok: false, problems: ['label must be valid or invalid'] };
      if (f.positive.length + f.negative.length >= MAX_EXAMPLES) return { ok: false, problems: [`at most ${MAX_EXAMPLES} examples per family`] };
      const { observation, reads, rolesRead } = await observe({ plan: f.plan, route, get });
      if (observation.status !== 'observed') return { ok: false, problems: [`nothing usable was observed: ${observation.reason}`] };
      (label === 'valid' ? f.positive : f.negative).push({ status: 'observed', facts: { ...observation.facts }, route: { name: route.name } });
      f.boundary = null;
      return { ok: true, reads, rolesRead, facts: observation.facts, valid: f.positive.length, invalid: f.negative.length };
    },
    learn(familyId) {
      const f = family(familyId);
      f.boundary = learnRepairBoundary({ positive: f.positive, negative: f.negative, intendedEffect: intendedEffect(familyId) });
      return f.boundary;
    },
    freeze() {
      const artifact = { schema: 'three-arm-repair-boundary-artifact/v1', application: 'erpnext', families: {} };
      for (const [id, f] of families) artifact.families[id] = { plan: f.plan, positive: f.positive, negative: f.negative,
        boundary: f.boundary ?? { status: 'abstain', reason: 'never-learned' } };
      const text = canonical(artifact);
      return { artifact, text, sha256: sha256(text) };
    },
  };
}

export function keptCases(artifact) {
  return Object.entries(artifact?.families ?? {}).flatMap(([familyId, f]) => [
    ...(f.positive ?? []).map(e => ({ familyId, name: e.route?.name, expect: 'write' })),
    ...(f.negative ?? []).map(e => ({ familyId, name: e.route?.name, expect: 'stop' })),
  ]).filter(c => typeof c.name === 'string');
}

export async function decide(artifact, route, get) {
  const f = artifact?.families?.[route.familyId];
  if (!f?.plan || f.boundary?.status !== 'learned') {
    return { decision: 'stop', reason: `no learned guard for this family (${f?.boundary?.reason ?? 'unknown family'})`, reads: 0 };
  }
  const { observation, reads } = await observe({ plan: f.plan, route, get });
  const verdict = checkRepairBoundary(f.boundary, observation, intendedEffect(route.familyId));
  return verdict.status === 'eligible-for-review' ? { decision: 'write', reason: 'guard holds', reads } : { decision: 'stop', reason: verdict.reason, reads };
}
