// The repair-boundary arm of the same-model three-arm test (clocksmith/deco#88).
//
// The model in this arm does not write a guard. It chooses which records to
// read (at most three reads per route), builds records it believes are valid
// and invalid under the policy, and labels them. `learnRepairBoundary`, unchanged
// from src/client, derives the guard from what those reads returned. On an unseen
// route the same reads are made and `checkRepairBoundary` answers.
//
// Two things here are part of the method and were fixed before any family existed:
//   - `projectOpenProjectHalScalars`, the hand-written OpenProject adapter from
//     Gates 3 and 4, which turns status and project links into numbers. It is
//     application-specific code whose authoring cost this test does not measure.
//   - the `intent` role: one fact, the hours the route asks to write, so that a
//     guard can compare the request with what an approving record says.
import { createHash } from 'node:crypto';
import { checkRepairBoundary, collectObservedFacts, learnRepairBoundary } from '../../../src/client/repair-boundary.js';
import { projectOpenProjectHalScalars } from '../repair-boundary-qualification.mjs';

export const MAX_READS = 3;
export const MAX_EXAMPLES = 24;
const ROLE = /^[a-z][a-z0-9_-]{0,47}$/;
const LINK = /^[A-Za-z][A-Za-z0-9]{0,47}$/;
const sha256 = text => createHash('sha256').update(text, 'utf8').digest('hex');
const canonical = value => JSON.stringify(value, (_, v) => (v && typeof v === 'object' && !Array.isArray(v)
  ? Object.fromEntries(Object.keys(v).sort().map(k => [k, v[k]])) : v));

/** The operation every route in a family asks for; examples and routes must name the same one. */
export const intendedEffect = familyId => `opbind-v1:${sha256(canonical({
  schema: 'three-arm-operation/v1', application: 'openproject', operation: 'set-work-hours', familyId,
}))}`;

/**
 * A read plan is up to three reads. Each has a role and either a `path` that may
 * hold `{target}` (the target work package's number), or `follow`: a link named
 * in the body of an earlier read, such as the target's parent.
 */
export function validateReadPlan(plan) {
  const problems = [];
  if (!Array.isArray(plan) || !plan.length || plan.length > MAX_READS) return [`a read plan holds 1 to ${MAX_READS} reads`];
  const roles = new Set();
  plan.forEach((read, index) => {
    const at = `reads[${index}]`;
    if (!read || typeof read !== 'object') return problems.push(`${at} is not an object`);
    if (typeof read.role !== 'string' || !ROLE.test(read.role) || read.role === 'intent') problems.push(`${at}.role must be a short lower-case name other than intent`);
    if (roles.has(read.role)) problems.push(`${at}.role is used twice`);
    const hasPath = typeof read.path === 'string';
    const hasFollow = read.follow && typeof read.follow === 'object';
    if (hasPath === Boolean(hasFollow)) problems.push(`${at} needs exactly one of path or follow`);
    if (hasPath && (!read.path.startsWith('/api/v3/') || /\{(?!target\})/.test(read.path))) problems.push(`${at}.path must start with /api/v3/ and may only use {target}`);
    if (hasFollow && (!roles.has(read.follow.role) || typeof read.follow.link !== 'string' || !LINK.test(read.follow.link))) {
      problems.push(`${at}.follow must name an earlier role and one of its links`);
    }
    roles.add(read.role);
  });
  return problems;
}

/** Makes the plan's reads for one route and returns what the learner is allowed to see. */
export async function observe({ plan, route, get }) {
  const bodies = new Map();
  const responses = [{ sameOrigin: true, method: 'GET', transport: 'fetch', status: 200, sourceRole: 'intent',
    json: { estimatedTime: `PT${route.workHours}H` } }];
  let reads = 0;
  for (const read of plan) {
    let path = null;
    if (typeof read.path === 'string') path = read.path.replaceAll('{target}', String(route.workPackageId));
    else {
      const href = bodies.get(read.follow.role)?._links?.[read.follow.link]?.href;
      if (typeof href === 'string' && href.startsWith('/api/v3/')) path = href;
    }
    if (!path) continue;
    reads += 1;
    const result = await get(path);
    if (!result?.ok || result.status < 200 || result.status >= 300 || !result.body || typeof result.body !== 'object') continue;
    bodies.set(read.role, result.body);
    responses.push({ sameOrigin: true, method: 'GET', transport: 'fetch', status: result.status, sourceRole: read.role,
      json: projectOpenProjectHalScalars(result.body) });
  }
  return { observation: collectObservedFacts(responses), reads, rolesRead: [...bodies.keys()] };
}

/** Holds one family's plan and examples while the model teaches; `freeze` returns the artifact. */
export function createTeacher(familyIds, restore = null) {
  // `restore` is an earlier artifact: maintenance after an upgrade starts from the work already frozen.
  const families = new Map(familyIds.map(id => {
    const kept = restore?.families?.[id];
    return [id, kept ? structuredClone({ plan: kept.plan, positive: kept.positive ?? [], negative: kept.negative ?? [],
      boundary: kept.boundary?.status === 'learned' ? kept.boundary : null })
      : { plan: null, positive: [], negative: [], boundary: null }];
  }));
  const family = id => {
    if (!families.has(id)) throw Error(`unknown family ${String(id).slice(0, 64)}`);
    return families.get(id);
  };
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
      // The work package is kept with the facts, so the example can be rerun after an upgrade.
      (label === 'valid' ? f.positive : f.negative).push({ status: 'observed', facts: { ...observation.facts },
        route: { project: route.project, workPackageId: route.workPackageId, workHours: route.workHours } });
      f.boundary = null;
      return { ok: true, reads, rolesRead, facts: observation.facts, valid: f.positive.length, invalid: f.negative.length };
    },
    learn(familyId) {
      const f = family(familyId);
      f.boundary = learnRepairBoundary({ positive: f.positive, negative: f.negative, intendedEffect: intendedEffect(familyId) });
      return f.boundary;
    },
    freeze() {
      const artifact = { schema: 'three-arm-repair-boundary-artifact/v1', families: {} };
      for (const [id, f] of families) {
        artifact.families[id] = { plan: f.plan, positive: f.positive, negative: f.negative,
          boundary: f.boundary ?? { status: 'abstain', reason: 'never-learned' } };
      }
      const text = canonical(artifact);
      return { artifact, text, sha256: sha256(text) };
    },
  };
}

/** The labelled examples kept in an artifact, as cases to rerun: what the guard must still say about each. */
export function keptCases(artifact) {
  return Object.entries(artifact?.families ?? {}).flatMap(([familyId, f]) => [
    ...(f.positive ?? []).map(e => ({ familyId, ...e.route, expect: 'write' })),
    ...(f.negative ?? []).map(e => ({ familyId, ...e.route, expect: 'stop' })),
  ]).filter(c => Number.isSafeInteger(c.workPackageId));
}

/** Decides one unseen route from a frozen artifact. No model call. Anything short of eligible is a stop. */
export async function decide(artifact, route, get) {
  const f = artifact?.families?.[route.familyId];
  if (!f?.plan || f.boundary?.status !== 'learned') {
    return { decision: 'stop', reason: `no learned guard for this family (${f?.boundary?.reason ?? 'unknown family'})`, reads: 0 };
  }
  const { observation, reads } = await observe({ plan: f.plan, route, get });
  const verdict = checkRepairBoundary(f.boundary, observation, intendedEffect(route.familyId));
  return verdict.status === 'eligible-for-review'
    ? { decision: 'write', reason: 'guard holds', reads }
    : { decision: 'stop', reason: verdict.reason, reads };
}
