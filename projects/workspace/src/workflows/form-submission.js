// Fawn workspace — controlled form submission workflow adapter
//
// Task logic only: fills named fields and submits once. The submission is an external effect
// identified by an effect key; retrying after an unknown outcome is the service's decision.

import { REJECTION_CODES } from '../errors.js';
import { canonicalJson, sha256Hex } from '../journal.js';
import { ACTION_STATUS, OUTCOMES } from '../state.js';
import { findElement } from './owner-session.js';

function formEffectKey(formUrl, fields) {
  return `form:${sha256Hex(canonicalJson({ formUrl, fields }))}`;
}

/**
 * @param {ReturnType<import('./owner-session.js').createOwnerSession>} session
 * @param {{runId: string, intent: string, formUrl: string, fields: Record<string, string>,
 *   completedWhen: object[], failedWhen?: object[], externalIdempotencyKey?: string,
 *   resubmissionOf?: string}} task
 */
async function runFormSubmission(session, task) {
  const { runId, intent, formUrl, fields, completedWhen, failedWhen = [] } = task;
  const steps = [];
  const effectKey = formEffectKey(formUrl, fields);
  const proceed = (record) => {
    steps.push(record);
    return record.outcome === OUTCOMES.COMPLETED;
  };

  const start = await session.observe();
  if (start.url !== formUrl && !proceed(await session.act(start, {
    actionId: `${runId}-open`,
    authorizedIntent: intent,
    kind: 'navigate',
    target: { url: formUrl },
  }))) {
    return { status: 'stopped', effectKey, steps };
  }

  const fieldSelectors = {};
  for (const [name, value] of Object.entries(fields)) {
    const current = await session.observe();
    const target = findElement(current, (element) => element.attributes.some(([key, val]) => key === 'name'
      && val === name), `field ${name}`);
    fieldSelectors[name] = target.selector;
    const record = await session.act(current, {
      actionId: `${runId}-fill-${name}`,
      authorizedIntent: intent,
      kind: 'fill',
      target,
      params: { value },
    });
    if (!proceed(record)) return { status: 'stopped', effectKey, steps };
  }

  const ready = await session.observe();
  const effect = { external: true, effectKey };
  if (task.externalIdempotencyKey) effect.externalIdempotencyKey = task.externalIdempotencyKey;
  const submission = await session.act(ready, {
    actionId: `${runId}-submit`,
    authorizedIntent: intent,
    kind: 'submit',
    target: findElement(ready, (element) => element.formAction && element.attributes.some(([key, val]) => key === 'type'
      && val === 'submit'), 'submit control'),
    preconditions: Object.entries(fields).map(([name, value]) => ({
      kind: 'input-value-equals',
      selector: fieldSelectors[name],
      value,
    })),
    effect,
    completion: { completedWhen, failedWhen },
    resubmissionOf: task.resubmissionOf,
  });
  steps.push(submission);
  return { status: submission.outcome ?? submission.dispatchStatus, effectKey, submission, steps };
}

/**
 * Finish a form task after an interruption. An earlier attempt with an uncertain outcome is
 * reconciled against the application's submissions page; only positive evidence of absence
 * leads to an explicit resubmission, and inconclusive evidence is left for human review.
 * @param {ReturnType<import('./owner-session.js').createOwnerSession>} session
 * @param {Parameters<typeof runFormSubmission>[1] & {submissionsUrl: string, submissionsSelector: string}} task
 */
async function recoverFormSubmission(session, task) {
  const effectKey = formEffectKey(task.formUrl, task.fields);
  const latest = (await session.outstanding()).filter((action) => action.effectKey === effectKey && action.kind === 'submit').at(-1);
  const resubmit = async (resubmissionOf, recovered) => ({
    ...await runFormSubmission(session, { ...task, runId: `${task.runId}-resubmit`, resubmissionOf }),
    recovered,
  });
  if (!latest) {
    try {
      return await runFormSubmission(session, task);
    } catch (error) {
      if (error.code === REJECTION_CODES.EFFECT_ALREADY_COMPLETED) return { status: OUTCOMES.COMPLETED, effectKey, recovered: 'already-completed', steps: [] };
      throw error;
    }
  }
  if (latest.outcome === OUTCOMES.COMPLETED || latest.outcome === OUTCOMES.FAILED) {
    return { status: latest.outcome, effectKey, recovered: 'recorded-outcome', steps: [] };
  }
  if (latest.dispatchStatus === ACTION_STATUS.NEVER_DISPATCHED) return resubmit(latest.actionId, 'resubmitted-never-dispatched');
  if (!latest.isUncertain) {
    return latest.reconciliation.result === 'effect-present'
      ? { status: OUTCOMES.COMPLETED, effectKey, recovered: 'earlier-reconciliation', steps: [] }
      : resubmit(latest.actionId, 'resubmitted-after-earlier-reconciliation');
  }
  const listing = await session.act(await session.observe(), {
    actionId: `${task.runId}-open-submissions`,
    authorizedIntent: task.intent,
    kind: 'navigate',
    target: { url: task.submissionsUrl },
  });
  if (listing.outcome !== OUTCOMES.COMPLETED) return { status: 'stopped', effectKey, steps: [listing] };
  const entry = `${task.fields.name} ${task.fields.email}`;
  const reconciled = await session.reconcile({
    actionId: latest.actionId,
    method: 'application-state',
    effectPresentWhen: [{ kind: 'element-text-includes', selector: task.submissionsSelector, value: entry }],
    effectAbsentWhen: [{ kind: 'element-text-excludes', selector: task.submissionsSelector, value: entry }],
  });
  const result = reconciled.reconciliation.result;
  if (result === 'effect-present') return { status: OUTCOMES.COMPLETED, effectKey, recovered: 'application-state', steps: [listing] };
  if (result === 'effect-absent') return resubmit(latest.actionId, 'resubmitted-after-absence');
  return { status: OUTCOMES.UNKNOWN, effectKey, recovered: 'human-review-needed', steps: [listing] };
}

export { formEffectKey, recoverFormSubmission, runFormSubmission };
