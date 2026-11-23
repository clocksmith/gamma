// Rebuilding an arm's kept cases on another ERPNext release (clocksmith/deco#88).
// DRAFT. Same idea as ../three-arm/regression.mjs: replay the arm's own write
// calls on a new database, then decide every kept case again with the frozen work.
// ERPNext names documents (PUR-ORD-2026-00003), and a new database may hand out
// different names, so each name a call created is mapped to the one it gets now.
export const MAX_KEPT_CASES = 24;

export function readGuardCases(value) {
  if (!Array.isArray(value)) return { cases: [], problems: ['tests.json must be a JSON array'] };
  const problems = [];
  const cases = [];
  const perFamily = new Map();
  value.forEach((c, index) => {
    const ok = c && typeof c === 'object' && typeof c.familyId === 'string' && typeof c.name === 'string' && ['write', 'stop'].includes(c.expect);
    if (!ok) return problems.push(`tests.json[${index}] needs familyId, name and expect`);
    const count = perFamily.get(c.familyId) ?? 0;
    if (count >= MAX_KEPT_CASES) return problems.push(`tests.json[${index}] is past the ${MAX_KEPT_CASES} cases kept for family ${c.familyId.slice(0, 64)}`);
    perFamily.set(c.familyId, count + 1);
    return cases.push({ familyId: c.familyId, name: c.name, expect: c.expect });
  });
  return { cases, problems };
}

const escapeRegExp = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const rewrite = (value, names) => {
  if (typeof value === 'string') {
    let out = value;
    // Longest first, and whole names only, so that one name is never rewritten inside another.
    for (const [then, now] of [...names].sort((a, b) => b[0].length - a[0].length)) {
      out = out.replace(new RegExp(`(?<![A-Za-z0-9-])${escapeRegExp(then)}(?![A-Za-z0-9-])`, 'g'), `\u0000${now}\u0000`);
    }
    return out.replaceAll('\u0000', '');
  }
  if (Array.isArray(value)) return value.map(v => rewrite(v, names));
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, rewrite(v, names)]));
  return value;
};

/**
 * A recorded body can hold a whole document as it was when the arm sent it,
 * including its modified time. ERPNext refuses a submit or an update whose
 * modified time is not the stored one, and on a rebuilt database it never is.
 * So a replayed submit sends the document as it is now, and a replayed update
 * drops the recorded modified time. Found on the first second-release probe,
 * where every replayed submit was refused with 417.
 */
async function freshen(call, path, body, request) {
  if (call.method === 'POST' && path.endsWith('/api/method/frappe.client.submit') && typeof body?.doc?.doctype === 'string' && typeof body.doc.name === 'string') {
    const now = await request(call.as, 'GET', `/api/resource/${encodeURIComponent(body.doc.doctype)}/${encodeURIComponent(body.doc.name)}`);
    if (now.status === 200 && now.body?.data) return { ...body, doc: now.body.data };
  }
  if (call.method === 'PUT' && body && typeof body === 'object' && 'modified' in body) {
    const { modified, ...rest } = body;
    return rest;
  }
  return body;
}

export async function rebuildRecords({ trace, request, names = new Map() }) {
  for (const [index, call] of trace.entries()) {
    const path = rewrite(call.path, names);
    const body = call.body === null ? undefined : await freshen(call, path, rewrite(call.body, names), request);
    const response = await request(call.as, call.method, path, body);
    if (response.status !== call.status) {
      return { rebuilt: false, names, failedAt: index, reason: `${call.method} ${path} answered ${response.status}, was ${call.status}` };
    }
    const now = response.body?.data?.name ?? response.body?.message?.name;
    if (call.name !== null && typeof now === 'string') names.set(call.name, now);
  }
  return { rebuilt: true, names, failedAt: null, reason: null };
}

export async function rerunKeptCases({ cases, trace, request, names = new Map(), decideCase }) {
  const rebuild = await rebuildRecords({ trace, request, names });
  const families = [...new Set(cases.map(c => c.familyId))];
  if (!rebuild.rebuilt) return { rebuilt: false, reason: rebuild.reason, results: [], failedFamilies: families, passed: 0, total: cases.length };
  const results = [];
  for (const kept of cases) {
    const name = rebuild.names.get(kept.name);
    if (name === undefined) { results.push({ ...kept, got: null, pass: false, reason: 'the document was not rebuilt' }); continue; }
    let got = 'stop';
    try { got = (await decideCase({ ...kept, name })).decision === 'write' ? 'write' : 'stop'; } catch { got = 'stop'; }
    results.push({ ...kept, name, got, pass: got === kept.expect });
  }
  return { rebuilt: true, reason: null, results, passed: results.filter(r => r.pass).length, total: results.length,
    failedFamilies: families.filter(id => results.some(r => r.familyId === id && !r.pass)) };
}
