// Reads sealed Fawn branches and decides whether one candidate may go to human review.
// It has no network or write authority. `review` never authorizes an action, and a branch's
// result is the branch's own claim, so anything uncertain ends in `abstain`.
const LIMITS = Object.freeze({ branches: 32, attempts: 64, list: 64, text: 200 });
export const OBSERVATION_SCHEMA = 'gammatron.fawn-branch-observation/v1';

const stringList = value => Array.isArray(value) && value.length <= LIMITS.list
  && value.every(entry => typeof entry === 'string' && entry.length <= LIMITS.text);
const snapshot = value => value !== null && typeof value === 'object'
  && stringList(value.alerts) && stringList(value.statuses) && stringList(value.dirty);
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
  return `(() => {
  const text = element => String(element.innerText ?? element.textContent ?? '').trim().replace(/\\s+/g, ' ').slice(0, ${LIMITS.text});
  const dirty = field => {
    if (field.matches('input[type=hidden],input[type=submit],input[type=button],input[type=reset],input[type=image]')) return false;
    if (field.matches('input[type=checkbox],input[type=radio]')) return field.checked !== field.defaultChecked;
    if (field.tagName === 'SELECT') return [...field.options].some(option => option.selected !== option.defaultSelected);
    return field.value !== field.defaultValue;
  };
  const list = selector => [...document.querySelectorAll(selector)].slice(0, ${LIMITS.list});
  const snap = () => ({ alerts: list('[role=alert],[role=alertdialog],dialog[open]').map(text),
    statuses: list('[role=status],output').map(text),
    dirty: list('input,textarea,select').filter(dirty).map(field => String(field.name || field.id || '(unnamed)').slice(0, ${LIMITS.text})).sort() });
  const before = snap();
  let thrown = null;
  try { (${action}); } catch (error) { thrown = String(error?.name ?? 'Error'); }
  return { schema: '${OBSERVATION_SCHEMA}', before, after: snap(), thrown };
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
  && snapshot(parsed.result.value.before) && snapshot(parsed.result.value.after);

function classify(candidate, ambient) {
  const parsed = parseBranchResult(candidate.text);
  const row = { id: candidate.id, verdict: 'no-result', detail: parsed.ended, effect: null };
  if (!usable(parsed)) return row;
  const observation = parsed.result.value;
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
    effect: JSON.stringify([expected.attempt, expected.target, [...observation.after.dirty].sort()]) };
}

/** Compares N branches with a no-op control. Pure and deterministic. */
export function verifyBranches({ control, candidates }) {
  const abstain = (reason, rows = []) => Object.freeze({ decision: 'abstain', reason, winner: null, effect: null, rows });
  if (!Array.isArray(candidates) || candidates.length === 0 || candidates.length > LIMITS.branches) return abstain('invalid-candidates');
  if (new Set(candidates.map(candidate => candidate?.id)).size !== candidates.length || candidates.some(candidate => typeof candidate?.id !== 'string')) return abstain('invalid-candidates');
  const baseline = parseBranchResult(control);
  if (!usable(baseline) || baseline.result.value.thrown !== null) return abstain('control-invalid');
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
