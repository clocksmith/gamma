// Reads sealed Fawn branches and decides whether one candidate may go to human review.
// It has no network or write authority. `review` never authorizes an action, and a branch's
// result is the branch's own claim, so anything uncertain ends in `abstain`.
const LIMITS = Object.freeze({ branches: 32, attempts: 64, list: 64, text: 200, url: 2048, bytes: 65536 });
export const OBSERVATION_SCHEMA = 'gammatron.fawn-branch-observation/v3';

const stringList = value => Array.isArray(value) && value.length <= LIMITS.list
  && value.every(entry => typeof entry === 'string' && entry.length <= LIMITS.text);
const valuePairs = value => Array.isArray(value) && value.length <= LIMITS.list
  && value.every(entry => Array.isArray(entry) && entry.length === 2 && entry.every(part => typeof part === 'string' && part.length <= LIMITS.text));
const snapshot = value => value !== null && typeof value === 'object' && typeof value.truncated === 'boolean'
  && stringList(value.alerts) && stringList(value.statuses) && stringList(value.dirty) && valuePairs(value.values);
const urlText = value => typeof value === 'string' && value.length <= LIMITS.url;
const intentShape = value => value !== null && typeof value === 'object' && typeof value.api === 'string' && urlText(value.target) && urlText(value.url)
  && typeof value.method === 'string' && value.body !== null && typeof value.body === 'object' && typeof value.body.kind === 'string'
  && Number.isSafeInteger(value.body.bytes) && valuePairs(value.body.fields);
const intentList = value => Array.isArray(value) && value.length <= LIMITS.attempts && value.every(intentShape);
const intentKey = intent => JSON.stringify([intent.method, intent.body.kind, intent.body.bytes, intent.body.fields]);
const added = (after, before) => {
  const remaining = [...before];
  return after.filter(entry => {
    const index = remaining.indexOf(entry);
    if (index < 0) return true;
    remaining.splice(index, 1);
    return false;
  });
};
const attemptKey = attempt => JSON.stringify([attempt.attempt, attempt.target]);

/** Wraps one action expression so the branch reports what the page showed before and after it. */
export function branchExpression(action) {
  if (typeof action !== 'string' || !action.trim()) throw new TypeError('action must be a JavaScript expression');
  // Async because a Fawn branch runs the script first and drains microtasks afterward. Values leave
  // the branch only as short digests, which compare effects but are not a security boundary.
  return `(async () => {
  const LIMIT = ${LIMITS.list}, TEXT = ${LIMITS.text};
  const text = element => String(element.innerText ?? element.textContent ?? '').trim().replace(/\\s+/g, ' ').slice(0, TEXT);
  const digest = value => {
    let a = 0xdeadbeef, b = 0x41c6ce57;
    for (let i = 0; i < value.length; i++) { const c = value.charCodeAt(i); a = Math.imul(a ^ c, 2654435761); b = Math.imul(b ^ c, 1597334677); }
    a = Math.imul(a ^ (a >>> 16), 2246822507) ^ Math.imul(b ^ (b >>> 13), 3266489909);
    b = Math.imul(b ^ (b >>> 16), 2246822507) ^ Math.imul(a ^ (a >>> 13), 3266489909);
    return (b >>> 0).toString(16).padStart(8, '0') + (a >>> 0).toString(16).padStart(8, '0');
  };
  const documents = () => {
    const found = [[document, '']];
    for (let i = 0; i < found.length && found.length <= LIMIT; i++) {
      [...found[i][0].querySelectorAll('iframe,frame')].forEach((frame, index) => {
        let child = null;
        try { child = frame.contentDocument; } catch {}
        if (child) found.push([child, found[i][1] + 'frame' + index + '/']);
      });
    }
    return found;
  };
  const valueOf = field => field.matches('input[type=checkbox],input[type=radio]') ? field.checked + ':' + field.value
    : field.tagName === 'SELECT' ? [...field.options].map(option => option.selected ? '1' : '0').join('') : String(field.value);
  const dirty = field => {
    if (field.matches('input[type=checkbox],input[type=radio]')) return field.checked !== field.defaultChecked;
    if (field.tagName === 'SELECT') return [...field.options].some(option => option.selected !== option.defaultSelected);
    return field.value !== field.defaultValue;
  };
  const snap = hiddenBefore => {
    const alerts = [], statuses = [], changed = [], hidden = new Map(), seen = new Map();
    for (const [root, prefix] of documents()) {
      alerts.push(...[...root.querySelectorAll('[role=alert],[role=alertdialog],dialog[open]')].map(text));
      statuses.push(...[...root.querySelectorAll('[role=status],output')].map(text));
      for (const field of root.querySelectorAll('input,textarea,select')) {
        if (field.matches('input[type=submit],input[type=button],input[type=reset],input[type=image]')) continue;
        const name = (prefix + String(field.name || field.id || '(unnamed)')).slice(0, TEXT);
        if (field.matches('input[type=hidden]')) {
          const count = seen.get(name) ?? 0;
          seen.set(name, count + 1);
          hidden.set(name + '#' + count, [name, digest(valueOf(field))]);
        } else if (dirty(field)) changed.push([name, digest(valueOf(field))]);
      }
    }
    if (hiddenBefore) {
      for (const [key, entry] of hidden) if (hiddenBefore.get(key)?.[1] !== entry[1]) changed.push(entry);
      for (const [key, entry] of hiddenBefore) if (!hidden.has(key)) changed.push([entry[0], 'removed']);
    }
    changed.sort((x, y) => x[0] < y[0] ? -1 : x[0] > y[0] ? 1 : x[1] < y[1] ? -1 : x[1] > y[1] ? 1 : 0);
    const truncated = alerts.length > LIMIT || statuses.length > LIMIT || changed.length > LIMIT;
    const values = changed.slice(0, LIMIT);
    return { hidden, view: { alerts: alerts.slice(0, LIMIT), statuses: statuses.slice(0, LIMIT), dirty: values.map(entry => entry[0]), values, truncated } };
  };
  // What the page's code asked to send. This is the branch's own claim; the browser's attempts stay authoritative.
  // A fetch bound before this wrapper runs is invisible here and ends as intent-missing, which is why a native
  // record in the browser is the stronger source.
  const URL_LIMIT = ${LIMITS.url}, BYTES = ${LIMITS.bytes}, DEPTH = 8;
  const intents = [], pendingForms = [];
  let intentsTruncated = false;
  const flatten = (value, path, out, depth) => {
    if (out.length > LIMIT) { intentsTruncated = true; return out; }
    if (value !== null && typeof value === 'object') {
      if (depth >= DEPTH) { intentsTruncated = true; out.push([path || '(body)', JSON.stringify(value)]); return out; }
      const entries = Array.isArray(value) ? value.map(item => ['[]', item]) : Object.entries(value);
      if (!entries.length) out.push([path || '(body)', JSON.stringify(value)]);
      for (const [key, item] of entries) flatten(item, key === '[]' ? path + '[]' : path ? path + '.' + key : key, out, depth + 1);
      return out;
    }
    out.push([path || '(body)', JSON.stringify(value) ?? String(value)]);
    return out;
  };
  const pairs = entries => {
    const fields = [];
    for (const [name, value] of entries) {
      const file = typeof File === 'function' && value instanceof File;
      fields.push([String(name).slice(0, TEXT), digest(file ? 'file:' + value.size : typeof value === 'string' ? value : JSON.stringify(value) ?? String(value))]);
    }
    if (fields.length > LIMIT) intentsTruncated = true;
    return fields.sort((x, y) => x[0] < y[0] ? -1 : x[0] > y[0] ? 1 : x[1] < y[1] ? -1 : x[1] > y[1] ? 1 : 0).slice(0, LIMIT);
  };
  const summarize = body => {
    if (body === null || body === undefined) return { kind: 'none', bytes: 0, fields: [] };
    if (typeof body === 'string') {
      const whole = [['(body)', digest(body)]];
      try {
        const parsed = JSON.parse(body);
        if (parsed && typeof parsed === 'object') return { kind: 'json', bytes: body.length, fields: pairs(flatten(parsed, '', [], 0)) };
      } catch {}
      if (/^[^=&\\s]+=[^&\\s]*(&[^=&\\s]+=[^&\\s]*)*$/.test(body)) return { kind: 'urlencoded', bytes: body.length, fields: pairs(new URLSearchParams(body)) };
      return { kind: 'text', bytes: body.length, fields: whole };
    }
    if (body instanceof URLSearchParams) return { kind: 'urlencoded', bytes: body.toString().length, fields: pairs(body) };
    if (body instanceof FormData) return { kind: 'formdata', bytes: 0, fields: pairs(body) };
    if (typeof Blob === 'function' && body instanceof Blob) return { kind: 'opaque', bytes: body.size, fields: [] };
    if (body instanceof ArrayBuffer || ArrayBuffer.isView(body)) {
      const bytes = body instanceof ArrayBuffer ? new Uint8Array(body) : new Uint8Array(body.buffer, body.byteOffset, body.byteLength);
      return bytes.length > BYTES ? { kind: 'opaque', bytes: bytes.length, fields: [] }
        : { kind: 'binary', bytes: bytes.length, fields: [['(body)', digest(String.fromCharCode(...bytes.subarray(0, 8192)) + ':' + bytes.length + ':' + bytes.reduce((sum, byte) => (sum * 31 + byte) >>> 0, 7))]] };
    }
    return { kind: 'opaque', bytes: 0, fields: [] };
  };
  const note = (root, api, target, method, body) => {
    const raw = String(target);
    let url = raw;
    try { url = new URL(raw, root.document.baseURI).href; } catch {}
    if (raw.length > URL_LIMIT || url.length > URL_LIMIT || intents.length >= ${LIMITS.attempts}) { intentsTruncated = true; return; }
    let summary;
    try { summary = summarize(body); } catch { summary = { kind: 'opaque', bytes: 0, fields: [] }; }
    intents.push({ api, target: raw, url, method: String(method || 'GET').toUpperCase().slice(0, 16), body: summary });
  };
  const formUrl = (root, form, submitter) => {
    const declared = submitter?.getAttribute?.('formaction') ?? form.getAttribute('action');
    try { return new URL(declared || root.location.href, root.document.baseURI).href; } catch { return String(declared ?? ''); }
  };
  const formMethod = (form, submitter) => submitter?.getAttribute?.('formmethod') || form.getAttribute('method') || 'GET';
  const watch = root => {
    // Reading a Request body needs a task a branch may never run, so keep the body given to its constructor.
    const NativeRequest = root.Request, requestBodies = new WeakMap();
    root.Request = new Proxy(NativeRequest, { construct(target, args, newTarget) {
      const made = Reflect.construct(target, args, newTarget);
      if (args[1] && 'body' in args[1]) requestBodies.set(made, args[1].body);
      else if (args[0] instanceof NativeRequest && requestBodies.has(args[0])) requestBodies.set(made, requestBodies.get(args[0]));
      return made;
    } });
    const nativeFetch = root.fetch;
    root.fetch = function (input, init) {
      const request = input instanceof NativeRequest ? input : null;
      const body = init && 'body' in init ? init.body : request && requestBodies.has(request) ? requestBodies.get(request) : request?.body ? new root.Blob() : null;
      note(root, 'fetch', request ? request.url : input, init?.method ?? request?.method ?? 'GET', body);
      return nativeFetch.apply(this, arguments);
    };
    const opened = new WeakMap(), xhr = root.XMLHttpRequest.prototype, nativeOpen = xhr.open, nativeSend = xhr.send;
    xhr.open = function (method, url) { opened.set(this, { method, url }); return nativeOpen.apply(this, arguments); };
    xhr.send = function (body) { const entry = opened.get(this); note(root, 'xhr', entry?.url ?? '', entry?.method ?? 'GET', body); return nativeSend.apply(this, arguments); };
    const nativeBeacon = root.navigator.sendBeacon?.bind(root.navigator);
    if (nativeBeacon) root.navigator.sendBeacon = (url, data) => { note(root, 'beacon', url, 'POST', data); return nativeBeacon(url, data); };
    const nativeSubmit = root.HTMLFormElement.prototype.submit;
    root.HTMLFormElement.prototype.submit = function () { note(root, 'form', formUrl(root, this), formMethod(this), new root.FormData(this)); return nativeSubmit.apply(this, arguments); };
    root.addEventListener('submit', event => pendingForms.push({ root, event, form: event.target, submitter: event.submitter ?? null }), true);
  };
  for (const [root] of documents()) { try { if (root.defaultView) watch(root.defaultView); } catch { intentsTruncated = true; } }
  const before = snap();
  let thrown = null;
  try { await (${action}); } catch (error) { thrown = String(error?.name ?? 'Error'); }
  for (let tick = 0; tick < 32; tick++) await null;
  for (const { root, event, form, submitter } of pendingForms) {
    if (event.defaultPrevented) continue;
    let data = null;
    try { data = new root.FormData(form, submitter ?? undefined); } catch { data = new root.Blob(); }
    note(root, 'form', formUrl(root, form, submitter), formMethod(form, submitter), data);
  }
  return { schema: '${OBSERVATION_SCHEMA}', before: before.view, after: snap(before.hidden).view, thrown, intents, intentsTruncated };
})()`;
}

/** One `Page.fawnBranchStatus` result: how it ended, a newline, then JSON lines. */
export function parseBranchResult(text) {
  const malformed = { ended: 'malformed', attempts: [], result: null };
  if (typeof text !== 'string') return malformed;
  const cut = text.indexOf('\n');
  const ended = cut < 0 ? text : text.slice(0, cut);
  const attempts = [];
  let result = null;
  try {
    for (const line of (cut < 0 ? '' : text.slice(cut + 1)).split('\n').filter(Boolean)) {
      const entry = JSON.parse(line);
      if (typeof entry?.attempt === 'string' && typeof entry.target === 'string') attempts.push({ attempt: entry.attempt, target: entry.target });
      else if (typeof entry?.ok === 'boolean' && result === null) result = entry;
      else return malformed;
    }
  } catch { return malformed; }
  return attempts.length > LIMITS.attempts ? malformed : { ended, attempts, result };
}

const usable = parsed => parsed.ended === 'finished' && parsed.result?.ok === true
  && parsed.result.value?.schema === OBSERVATION_SCHEMA
  && snapshot(parsed.result.value.before) && snapshot(parsed.result.value.after)
  && intentList(parsed.result.value.intents) && typeof parsed.result.value.intentsTruncated === 'boolean';

// The page-side record of the one browser-recorded write, checked against what the candidate declared.
function checkIntent(observation, attempt, expected) {
  const matching = observation.intents.filter(intent => intent.api === attempt.attempt && (intent.target === attempt.target || intent.url === attempt.target));
  if (new Set(matching.map(intentKey)).size > 1) return { verdict: 'unexpected-effect', detail: 'the page recorded different bodies for one write' };
  const intent = matching[0] ?? null;
  const declared = expected.method !== undefined || expected.bodyFields !== undefined;
  if (!declared) return { intent };
  if (observation.intentsTruncated) return { verdict: 'observation-truncated', detail: 'the write could not be recorded in full' };
  if (!intent) return { verdict: 'intent-missing', detail: 'the browser recorded a write the page-side record did not see' };
  if (expected.method !== undefined && intent.method !== String(expected.method).toUpperCase()) return { verdict: 'intent-mismatch', detail: `method ${intent.method}` };
  if (expected.bodyFields !== undefined) {
    if (intent.body.kind === 'opaque') return { verdict: 'intent-opaque', detail: 'the write body could not be read' };
    const names = [...new Set(intent.body.fields.map(field => field[0]))].sort();
    const wanted = [...new Set(expected.bodyFields)].sort();
    if (JSON.stringify(names) !== JSON.stringify(wanted)) return { verdict: 'unexpected-body-field', detail: names.join(', ').slice(0, LIMITS.text) };
  }
  return { intent };
}

function classify(candidate, ambient) {
  const parsed = parseBranchResult(candidate.text);
  const row = { id: candidate.id, verdict: 'no-result', detail: parsed.ended, effect: null };
  if (!usable(parsed)) return row;
  const observation = parsed.result.value;
  if (observation.before.truncated || observation.after.truncated) return { ...row, verdict: 'observation-truncated', detail: 'the page has more entries than the observation can hold' };
  const remaining = [...ambient];
  const extra = parsed.attempts.filter(attempt => {
    const index = remaining.indexOf(attemptKey(attempt));
    if (index < 0) return true;
    remaining.splice(index, 1);
    return false;
  });
  const fail = (verdict, detail) => ({ ...row, verdict, detail });
  if (extra.length === 0) return fail('no-effect', 'the branch attempted nothing beyond the control');
  const expected = candidate.expect;
  if (extra.length !== 1 || extra[0].attempt !== expected?.attempt || extra[0].target !== expected?.target) {
    return fail('unexpected-effect', extra.map(attempt => `${attempt.attempt} ${attempt.target}`).join(', ').slice(0, LIMITS.text));
  }
  if (observation.thrown !== null && observation.thrown !== 'NotAllowedError') return fail('action-threw', String(observation.thrown).slice(0, LIMITS.text));
  const checked = checkIntent(observation, extra[0], expected);
  if (checked.verdict) return fail(checked.verdict, checked.detail);
  const alerts = added(observation.after.alerts, observation.before.alerts);
  if (alerts.length) return fail('page-warned', alerts[0]);
  const allowedStatuses = candidate.statuses ?? [];
  const statuses = added(observation.after.statuses, observation.before.statuses).filter(entry => !allowedStatuses.includes(entry));
  if (statuses.length) return fail('status-changed', statuses[0]);
  const fields = new Set(candidate.fields ?? []);
  const dirty = observation.after.dirty.filter(name => !fields.has(name));
  if (dirty.length) return fail('unexpected-dirty-field', dirty.join(', ').slice(0, LIMITS.text));
  if (candidate.accepts) {
    let accepted = false;
    try { accepted = candidate.accepts(observation) === true; } catch { accepted = false; }
    if (!accepted) return fail('wrong-outcome', 'the candidate check did not accept the result');
  }
  return { ...row, verdict: 'eligible', detail: null,
    effect: JSON.stringify([expected.attempt, expected.target, observation.after.values, checked.intent ? intentKey(checked.intent) : null]) };
}

/** Compares N branches with a no-op control. Pure and deterministic. */
export function verifyBranches({ control, candidates }) {
  const abstain = (reason, rows = []) => Object.freeze({ decision: 'abstain', reason, winner: null, effect: null, rows });
  if (!Array.isArray(candidates) || candidates.length === 0 || candidates.length > LIMITS.branches) return abstain('invalid-candidates');
  if (new Set(candidates.map(candidate => candidate?.id)).size !== candidates.length || candidates.some(candidate => typeof candidate?.id !== 'string')) return abstain('invalid-candidates');
  const baseline = parseBranchResult(control);
  if (!usable(baseline) || baseline.result.value.thrown !== null || baseline.result.value.after.truncated) return abstain('control-invalid');
  const ambient = baseline.attempts.map(attemptKey);
  const rows = candidates.map(candidate => classify(candidate, ambient));
  const eligible = rows.filter(row => row.verdict === 'eligible');
  if (eligible.length === 0) return abstain('none-eligible', rows);
  if (new Set(eligible.map(row => row.effect)).size > 1) return abstain('ambiguous-effects', rows);
  return Object.freeze({ decision: 'eligible', reason: null, winner: eligible[0].id, effect: eligible[0].effect, rows });
}

/** Adds one read-only prerequisite check on the winner. A branch cannot see the server, so this step must pass. */
export async function decideBranch({ control, candidates, attest }) {
  const verified = verifyBranches({ control, candidates });
  if (verified.decision !== 'eligible') return verified;
  const abstain = reason => Object.freeze({ ...verified, decision: 'abstain', reason, winner: null, effect: null });
  if (typeof attest !== 'function') return abstain('attestation-required');
  let answer;
  try { answer = await attest({ winner: verified.winner, effect: verified.effect }); } catch { return abstain('attestation-failed'); }
  if (answer?.holds !== true) return abstain('prerequisite-not-confirmed');
  return Object.freeze({ ...verified, decision: 'review', facts: answer.facts ?? null });
}
