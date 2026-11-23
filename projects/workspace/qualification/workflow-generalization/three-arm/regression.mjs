// Rerunning an arm's kept cases on another release (clocksmith/deco#88,
// same-model three-arm test).
//
// During discovery each arm builds work packages and says what should happen on
// them: the repair-boundary arm by labelling examples, the guard-writing arm in
// tests.json. Those cases are kept beside the frozen work, with the arm's own
// write calls. On an upgraded release the database is new, so the records are
// rebuilt by replaying those calls, and each case is decided again by the same
// frozen work. A family whose cases cannot be rebuilt, or no longer come out as
// they did, must not be reused until the arm's maintenance has dealt with it.
// The same mechanism serves both arms.
// Per family, the same number of labelled examples the repair-boundary arm may keep.
export const MAX_KEPT_CASES = 24;

/** Shape check for tests.json from the guard-writing arm. Returns { cases, problems }. */
export function readGuardCases(value) {
  if (!Array.isArray(value)) return { cases: [], problems: ['tests.json must be a JSON array'] };
  const problems = [];
  const cases = [];
  const perFamily = new Map();
  value.forEach((c, index) => {
    const ok = c && typeof c === 'object' && typeof c.familyId === 'string' && typeof c.project === 'string'
      && Number.isSafeInteger(c.workPackageId) && Number.isSafeInteger(c.workHours) && ['write', 'stop'].includes(c.expect);
    if (!ok) return problems.push(`tests.json[${index}] needs familyId, project, workPackageId, workHours and expect`);
    const count = perFamily.get(c.familyId) ?? 0;
    if (count >= MAX_KEPT_CASES) return problems.push(`tests.json[${index}] is past the ${MAX_KEPT_CASES} cases kept for family ${c.familyId.slice(0, 64)}`);
    perFamily.set(c.familyId, count + 1);
    return cases.push({ familyId: c.familyId, project: c.project, workPackageId: c.workPackageId, workHours: c.workHours, expect: c.expect });
  });
  return { cases, problems };
}

const rewrite = (value, ids) => {
  if (typeof value === 'string') return value.replace(/(\/work_packages\/)(\d+)/g, (whole, prefix, id) => (ids.has(Number(id)) ? prefix + ids.get(Number(id)) : whole));
  if (Array.isArray(value)) return value.map(v => rewrite(v, ids));
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, rewrite(v, ids)]));
  return value;
};

/**
 * Replays the kept write calls in order. Work package numbers differ on a new
 * database, so each number a call created is mapped to the one it gets now, and
 * later calls are rewritten. `ids` starts with the disclosed examples' mapping.
 * A call that does not answer as it did before stops the rebuild.
 */
export async function rebuildRecords({ trace, request, ids = new Map() }) {
  for (const [index, call] of trace.entries()) {
    const path = rewrite(call.path, ids);
    const response = await request(call.as, call.method, path, call.body === null ? undefined : rewrite(call.body, ids));
    if (response.status !== call.status) {
      return { rebuilt: false, ids, failedAt: index, reason: `${call.method} ${path} answered ${response.status}, was ${call.status}` };
    }
    if (call.id !== null && Number.isSafeInteger(response.body?.id)) ids.set(call.id, response.body.id);
  }
  return { rebuilt: true, ids, failedAt: null, reason: null };
}

/**
 * Rebuilds, then decides every kept case with `decideCase(case)`, which resolves
 * to { decision }. Returns each case's outcome and the families that must not be reused.
 */
export async function rerunKeptCases({ cases, trace, request, ids = new Map(), decideCase }) {
  const rebuild = await rebuildRecords({ trace, request, ids });
  const families = [...new Set(cases.map(c => c.familyId))];
  if (!rebuild.rebuilt) {
    return { rebuilt: false, reason: rebuild.reason, results: [], failedFamilies: families, passed: 0, total: cases.length };
  }
  const results = [];
  for (const kept of cases) {
    const workPackageId = rebuild.ids.get(kept.workPackageId);
    if (workPackageId === undefined) {
      results.push({ ...kept, got: null, pass: false, reason: 'the work package was not rebuilt' });
      continue;
    }
    let got = 'stop';
    try { got = (await decideCase({ ...kept, workPackageId })).decision === 'write' ? 'write' : 'stop'; } catch { got = 'stop'; }
    results.push({ ...kept, workPackageId, got, pass: got === kept.expect });
  }
  return { rebuilt: true, reason: null, results, passed: results.filter(r => r.pass).length, total: results.length,
    failedFamilies: families.filter(id => results.some(r => r.familyId === id && !r.pass)) };
}
