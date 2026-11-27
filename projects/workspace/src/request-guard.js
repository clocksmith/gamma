// Fawn workspace — request-level write guard
//
// While the commit gate dispatches an approved commit, every non-GET/HEAD request the page sends
// is held at the browser (CDP Fetch domain) and compared with the approval's request rule before
// it may leave: method and URL, the approved body values, and the approved version at the body
// path the approval names. JSON, urlencoded and multipart/form-data bodies are read; a body that
// cannot be read exactly is refused. One matching write continues; anything else fails in the browser with
// BlockedByClient and is reported. Paths and values are data from the approval; no application
// is named here.

import { createHash } from 'node:crypto';
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

/** Body bytes of a paused request, or null when the browser did not hand them over. */
function bodyBytes(request) {
  if (Array.isArray(request.postDataEntries)) {
    return Buffer.concat(request.postDataEntries.map(entry => Buffer.from(entry?.bytes ?? '', 'base64')));
  }
  if (typeof request.postData === 'string') return Buffer.from(request.postData, 'utf8');
  return null;
}

function contentType(request) {
  const headers = request.headers && typeof request.headers === 'object' ? request.headers : {};
  const entry = Object.entries(headers).find(([name]) => name.toLowerCase() === 'content-type');
  return typeof entry?.[1] === 'string' ? entry[1] : '';
}

const MULTIPART = /^multipart\/form-data\s*;(.*)$/i;
const BOUNDARY = /(?:^|;)\s*boundary=(?:"([^"]{1,70})"|([^\s";]{1,70}))\s*(?:;|$)/i;
const DISPOSITION = /^form-data\s*;\s*name="([^"]*)"(?:\s*;\s*filename="([^"]*)")?\s*$/i;

/**
 * [path, value] pairs of a multipart/form-data body (RFC 7578), or null when it cannot be read
 * exactly. Text parts read like urlencoded fields; a file part (a filename or its own content type)
 * becomes { file: { filename, contentType, byteLength, sha256 } }, which passes only where the
 * approval names its path: that exact file in `fields`, or the path in `allowPaths`. Bytes are split
 * as latin1 so binary parts stay exact.
 */
function multipartPairs(params, bytes) {
  const match = BOUNDARY.exec(params);
  if (!match) return null;
  const delimiter = `--${match[1] ?? match[2]}`;
  const text = bytes.toString('latin1');
  if (!text.startsWith(delimiter)) return null;
  const out = [];
  let at = delimiter.length;
  for (;;) {
    if (text.startsWith('--', at)) {
      const rest = text.slice(at + 2);
      return rest === '' || rest === '\r\n' ? out : null;
    }
    if (!text.startsWith('\r\n', at)) return null;
    const end = text.indexOf(`\r\n${delimiter}`, at + 2);
    if (end < 0) return null;
    const part = text.slice(at + 2, end);
    at = end + 2 + delimiter.length;
    const split = part.indexOf('\r\n\r\n');
    if (split < 0) return null;
    const headers = new Map();
    for (const line of part.slice(0, split).split('\r\n')) {
      const colon = line.indexOf(':');
      const name = colon > 0 ? line.slice(0, colon).trim().toLowerCase() : '';
      if (!['content-disposition', 'content-type'].includes(name) || headers.has(name)) return null;
      headers.set(name, line.slice(colon + 1).trim());
    }
    const disposition = DISPOSITION.exec(headers.get('content-disposition') ?? '');
    if (!disposition || !disposition[1]) return null;
    const name = Buffer.from(disposition[1], 'latin1').toString('utf8');
    const raw = Buffer.from(part.slice(split + 4), 'latin1');
    if (disposition[2] !== undefined || headers.has('content-type')) {
      out.push([name, { file: { filename: Buffer.from(disposition[2] ?? '', 'latin1').toString('utf8'),
        contentType: headers.get('content-type') ?? null, byteLength: raw.length,
        sha256: createHash('sha256').update(raw).digest('hex') } }]);
    } else if (!flatten(raw.toString('utf8'), name, out, 1)) return null;
  }
}

/** [path, value] pairs of a JSON, form-encoded or multipart body, or null when it cannot be read exactly. */
function bodyPairs(request) {
  const bytes = bodyBytes(request);
  if (!bytes || bytes.length > MAX_BODY_CHARS) return null;
  const multipart = MULTIPART.exec(contentType(request));
  if (multipart) return multipartPairs(multipart[1], bytes);
  const text = bytes.toString('utf8');
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
  const pairs = bodyPairs(request);
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
