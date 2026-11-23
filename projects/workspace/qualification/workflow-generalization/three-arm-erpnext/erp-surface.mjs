// The only way an ERPNext arm session reaches the application (clocksmith/deco#88).
// DRAFT, outside the frozen runner hash. Same rules as the OpenProject door in
// ../three-arm/app-surface.mjs: one instance, the two test accounts, bounded calls
// in discovery, read-only as the approver with a few reads when deciding, and a
// log of every call, refused or not, that the session cannot reach.
import { ALLOWED_PATH } from './erp-app.mjs';

export const ERP_LIMITS = Object.freeze({
  discovery: Object.freeze({ requests: 400, recordsCreated: 60 }),
  decision: Object.freeze({ reads: 8 }),
  pathChars: 512, bodyBytes: 16384, responseChars: 60000,
});
const DISCOVERY_METHODS = new Set(['GET', 'POST', 'PUT', 'DELETE']);
const CREATES_RECORD = /^\/api\/resource\/[A-Za-z%0-9 _-]+(?:\?.*)?$/;

/** Returns the reason a path is refused, or null. Reading is limited to documents; no method call may be read. */
export function refuseErpPath(path, { readOnly = false, limit = ERP_LIMITS.pathChars } = {}) {
  if (typeof path !== 'string' || !path) return 'path must be a string';
  if (path.length > limit) return 'path is too long';
  if (/[\\\u0000-\u001f\u007f#]/.test(path)) return 'path holds a character that is not allowed';
  const route = path.split('?')[0];
  if (/%(?:2f|5c|2e|00|25)/i.test(route) || route.includes('..') || route.includes('//')) return 'path holds a separator or dot that is not allowed';
  if (!ALLOWED_PATH.test(path)) return 'path must be /api/resource/<DocType>[/<name>] or frappe.client.submit / cancel';
  if (readOnly && !route.startsWith('/api/resource/')) return 'only documents can be read';
  return null;
}

export function createErpSurface({ mode, request, log = () => {}, trace = () => {}, limits = ERP_LIMITS, now = () => new Date().toISOString() }) {
  if (!['discovery', 'decision'].includes(mode)) throw Error('mode must be discovery or decision');
  const counts = { requests: 0, reads: 0, recordsCreated: 0, refused: 0 };
  const refuse = (entry, reason) => { counts.refused += 1; log({ at: now(), mode, ...entry, refused: reason }); return { ok: false, refused: reason }; };
  const forward = async (account, method, path, body) => {
    const response = await request(account, method, path, body);
    let text = JSON.stringify(response.body ?? null);
    const truncated = text.length > limits.responseChars;
    if (truncated) text = text.slice(0, limits.responseChars);
    log({ at: now(), mode, as: account, method, path, status: response.status });
    if (method !== 'GET') trace({ as: account, method, path, body: body ?? null, status: response.status,
      name: typeof response.body?.data?.name === 'string' ? response.body.data.name : typeof response.body?.message?.name === 'string' ? response.body.message.name : null });
    return { ok: true, status: response.status, body: truncated ? undefined : response.body, ...(truncated ? { bodyText: text, truncated: true } : {}) };
  };
  const tools = mode === 'decision' ? {
    erp_get: async ({ path } = {}) => {
      const entry = { as: 'approver', method: 'GET', path: typeof path === 'string' ? path.slice(0, limits.pathChars) : null };
      const reason = refuseErpPath(path, { readOnly: true, limit: limits.pathChars });
      if (reason) return refuse(entry, reason);
      if (counts.reads >= limits.decision.reads) return refuse(entry, `read limit of ${limits.decision.reads} reached`);
      counts.reads += 1;
      return forward('approver', 'GET', path);
    },
  } : {
    erp_request: async ({ as, method, path, body } = {}) => {
      const entry = { as: typeof as === 'string' ? as.slice(0, 16) : null, method: typeof method === 'string' ? method.slice(0, 8) : null,
        path: typeof path === 'string' ? path.slice(0, limits.pathChars) : null };
      if (!['author', 'approver'].includes(as)) return refuse(entry, 'as must be author or approver');
      if (!DISCOVERY_METHODS.has(method)) return refuse(entry, 'method must be GET, POST, PUT or DELETE');
      const reason = refuseErpPath(path, { readOnly: method === 'GET', limit: limits.pathChars });
      if (reason) return refuse(entry, reason);
      if (body !== undefined && (body === null || typeof body !== 'object' || Array.isArray(body) || JSON.stringify(body).length > limits.bodyBytes)) {
        return refuse(entry, `body must be an object of at most ${limits.bodyBytes} bytes`);
      }
      if (method === 'GET' && body !== undefined) return refuse(entry, 'a GET takes no body');
      if (counts.requests >= limits.discovery.requests) return refuse(entry, `request limit of ${limits.discovery.requests} reached`);
      const creates = method === 'POST' && CREATES_RECORD.test(path);
      if (creates && counts.recordsCreated >= limits.discovery.recordsCreated) return refuse(entry, `record limit of ${limits.discovery.recordsCreated} reached`);
      counts.requests += 1;
      const result = await forward(as, method, path, body);
      if (creates && result.status === 200) counts.recordsCreated += 1;
      return result;
    },
  };
  return Object.freeze({ mode, tools, counts: () => ({ ...counts }) });
}

export const ERP_TOOL_DEFINITIONS = Object.freeze({
  erp_request: {
    name: 'erp_request',
    description: 'Make one ERPNext REST call on the instance under test, as the author or the approver test account. This is the only way to reach the application. '
      + 'Allowed: /api/resource/<DocType>[/<name>] and /api/method/frappe.client.submit or frappe.client.cancel. Returns the HTTP status and the JSON body.',
    inputSchema: { type: 'object', additionalProperties: false, required: ['as', 'method', 'path'], properties: {
      as: { type: 'string', enum: ['author', 'approver'] },
      method: { type: 'string', enum: ['GET', 'POST', 'PUT', 'DELETE'] },
      path: { type: 'string', description: 'For example /api/resource/Purchase%20Order/<name>. A query string is allowed.' },
      body: { type: 'object', description: 'JSON body for POST and PUT.' },
    } },
  },
  erp_get: {
    name: 'erp_get',
    description: 'Read one ERPNext document on the instance under test, as the approver. Read-only, and only a few reads are allowed. Returns the HTTP status and the JSON body.',
    inputSchema: { type: 'object', additionalProperties: false, required: ['path'], properties: {
      path: { type: 'string', description: '/api/resource/<DocType>/<name>. A query string is allowed.' },
    } },
  },
});
