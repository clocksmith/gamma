// Fawn workspace — request-level write guard
//
// While the commit gate dispatches an approved commit, every non-GET/HEAD request the page sends
// is held at the browser (CDP Fetch domain) and compared with the approval's request rule before
// it may leave: method and URL, the approved body values, and the approved version at the body
// path the approval names. One matching write continues; anything else fails in the browser with
// BlockedByClient and is reported. Paths and values are data from the approval; no application
// is named here.

import { expectedBodyFields } from './client/branch-verifier.js';
import { canonicalJson } from './journal.js';

const READ_METHODS = new Set(['GET', 'HEAD', 'OPTIONS']);
const MAX_BODY_CHARS = 1 << 20;
const MAX_DEPTH = 8;
const refusal = (reason, details = {}) => Object.freeze({ ok: false, reason, ...details });

function href(url) {
  try { return new URL(url).href; } catch { return null; }
}

/** The request rule an approval may carry: { method, url, fields, versionPath, allowPaths? }. */
function validRequestRule(rule) {
  return rule !== null && typeof rule === 'object' && typeof rule.method === 'string' && /^[A-Za-z]{1,16}$/.test(rule.method)
    && !READ_METHODS.has(rule.method.toUpperCase()) && href(rule.url) === rule.url
    && rule.fields !== null && typeof rule.fields === 'object' && !Array.isArray(rule.fields)
    && typeof rule.versionPath === 'string' && rule.versionPath.length > 0
    && (rule.allowPaths === undefined || (Array.isArray(rule.allowPaths) && rule.allowPaths.every(path => typeof path === 'string' && path)));
}

// A string value that is itself a JSON object or array (a document sent as one form or JSON field)
// is read through, so `doc.modified` names the version inside it.
function nested(value) {
  if (typeof value !== 'string' || !/^\s*[{[]/.test(value)) return undefined;
  try { const parsed = JSON.parse(value); return parsed && typeof parsed === 'object' ? parsed : undefined; } catch { return undefined; }
}

function flatten(value, path, out, depth) {
  const inner = depth > 0 ? nested(value) : undefined;
  const node = inner ?? value;
  if (node !== null && typeof node === 'object') {
    if (depth >= MAX_DEPTH) return false;
    const entries = Array.isArray(node) ? node.map(item => ['[]', item]) : Object.entries(node);
    if (!entries.length) out.push([path || '(body)', node]);
    for (const [key, item] of entries) {
      if (!flatten(item, key === '[]' ? `${path}[]` : path ? `${path}.${key}` : key, out, depth + 1)) return false;
    }
    return true;
  }
  out.push([path || '(body)', node]);
  return true;
}

/** Body text of a paused request, or null when the browser did not hand it over. */
function bodyText(request) {
  if (typeof request.postData === 'string') return request.postData;
  if (Array.isArray(request.postDataEntries)) {
    return request.postDataEntries.map(entry => Buffer.from(entry?.bytes ?? '', 'base64').toString('utf8')).join('');
  }
  return null;
}

/** [path, value] pairs of a JSON or form-encoded body, or null when it cannot be read exactly. */
function bodyPairs(text) {
  if (typeof text !== 'string' || text.length > MAX_BODY_CHARS) return null;
  const shape = expectedBodyFields(text);
  if (shape.truncated || !['json', 'urlencoded'].includes(shape.kind)) return null;
  const out = [];
  if (shape.kind === 'json') return flatten(JSON.parse(text), '', out, 0) ? out : null;
  for (const [key, value] of new URLSearchParams(text)) if (!flatten(value, key, out, 1)) return null;
  return out;
}

const allowed = (rule, path) => (rule.allowPaths ?? []).some(entry =>
  entry.endsWith('.*') ? path.startsWith(entry.slice(0, -1)) : path === entry);

/**
 * Pure decision for one paused request against the rule and the approved version. Reads pass.
 * Returns { ok, write } or a refusal: unexpected-write (method or URL), request-payload-mismatch
 * (unreadable body, an approved value missing or different, or an unapproved field),
 * request-version-mismatch (the version at `versionPath` missing, repeated or not the approved one).
 */
function checkWriteRequest(rule, version, request) {
  const method = String(request?.method ?? '').toUpperCase();
  if (READ_METHODS.has(method)) return Object.freeze({ ok: true, write: false });
  if (method !== rule.method.toUpperCase() || href(request.url) !== rule.url) {
    return refusal('unexpected-write', { method, url: href(request?.url) });
  }
  const pairs = bodyPairs(bodyText(request));
  if (!pairs) return refusal('request-payload-mismatch', { detail: 'unreadable body' });
  const at = path => pairs.filter(([key]) => key === path).map(([, value]) => value);
  const versions = at(rule.versionPath);
  if (versions.length !== 1 || versions[0] === null || typeof versions[0] === 'object' || String(versions[0]) !== String(version)) {
    return refusal('request-version-mismatch', { path: rule.versionPath });
  }
  for (const [path, expected] of Object.entries(rule.fields)) {
    const values = at(path);
    if (values.length !== 1 || canonicalJson(values[0]) !== canonicalJson(expected)) return refusal('request-payload-mismatch', { path });
  }
  const extra = [...new Set(pairs.map(([key]) => key))].filter(path => path !== rule.versionPath
    && !Object.hasOwn(rule.fields, path) && !allowed(rule, path));
  if (extra.length) return refusal('request-payload-mismatch', { extra });
  return Object.freeze({ ok: true, write: true });
}

/**
 * Holds every request on one CDP page session while `run` performs the commit click, admits at most
 * one write that passes `checkWriteRequest`, and fails every other write with BlockedByClient.
 * After `run`, it keeps holding for `windowMs` (or until a write was decided, then `settleMs`) so a
 * write the click starts asynchronously is still judged. Fetch.disable always runs. `session` is
 * { send(method, params), subscribe(listener) -> unsubscribe }, listener(method, params).
 */
async function guardWrites(session, { rule, version, windowMs, settleMs, pollMs = 5 }, run) {
  const decisions = [];
  let admitted = 0;
  const pending = new Set();
  const decide = async params => {
    const verdict = checkWriteRequest(rule, version, params.request);
    const { method, url } = params.request ?? {};
    if (verdict.ok && !verdict.write) return session.send('Fetch.continueRequest', { requestId: params.requestId });
    if (verdict.ok && admitted === 0) {
      admitted += 1;
      decisions.push({ outcome: 'continued', method, url });
      return session.send('Fetch.continueRequest', { requestId: params.requestId });
    }
    // Only one write per approval: a second matching write is as unexpected as a wrong one.
    decisions.push({ outcome: 'blocked', reason: verdict.ok ? 'unexpected-write' : verdict.reason, method, url,
      ...(verdict.ok ? { detail: 'second write' } : {}) });
    return session.send('Fetch.failRequest', { requestId: params.requestId, errorReason: 'BlockedByClient' });
  };
  const unsubscribe = session.subscribe((method, params) => {
    if (method !== 'Fetch.requestPaused') return;
    const task = decide(params).catch(error => {
      decisions.push({ outcome: 'blocked', reason: 'request-guard-error', detail: String(error?.message ?? error) });
    }).finally(() => pending.delete(task));
    pending.add(task);
  });
  const writes = () => decisions.length;
  let result, failure = null;
  try {
    await session.send('Fetch.enable', { patterns: [{ urlPattern: '*', requestStage: 'Request' }] });
    result = await run();
    for (let waited = 0; waited < windowMs && writes() === 0; waited += pollMs) await new Promise(r => setTimeout(r, pollMs));
    if (writes() > 0) await new Promise(r => setTimeout(r, settleMs));
    while (pending.size) await Promise.allSettled([...pending]);
  } catch (error) {
    failure = error;
  } finally {
    // Disable while still listening, so a request paused in the last moment is still decided.
    try { await session.send('Fetch.disable'); } catch (error) { failure ??= error; }
    await Promise.allSettled([...pending]);
    unsubscribe();
  }
  const blocked = decisions.filter(entry => entry.outcome === 'blocked');
  const report = Object.freeze({ admitted, blocked, decisions });
  if (failure) throw Object.assign(failure, { requestGuard: report });
  return { result, requestGuard: report };
}

export { checkWriteRequest, guardWrites, validRequestRule };
