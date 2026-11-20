// Fawn workspace — engineering investigation workflow adapter
//
// Task logic only: inspects an incident page and authorized runbook/telemetry links, binds
// observed source digests, files one precondition-checked disposition, optionally exports the
// postmortem bundle, and reconciles interrupted submissions against the incident audit log
// without blind retries.

import { REJECTION_CODES } from '../errors.js';
import { canonicalJson, sha256Hex } from '../journal.js';
import { ACTION_STATUS, OUTCOMES } from '../state.js';
import { findElement } from './owner-session.js';

const LINE_BREAK = /\n+/;

function investigationEffectKey(incidentUrl, dispositionFields) {
  return `investigation:${sha256Hex(canonicalJson({ incidentUrl, dispositionFields }))}`;
}

function settledOrStop(record, steps) {
  steps.push(record);
  return record.outcome === OUTCOMES.COMPLETED;
}

async function exportBundle(session, { runId, intent, artifactUrl = null, artifactLinkText }, steps) {
  if (!artifactLinkText) return { ok: true, artifact: null };
  let page = await session.observe();
  if (artifactUrl && page.url !== artifactUrl) {
    const opened = await session.act(page, {
      actionId: `${runId}-artifact-open`,
      authorizedIntent: intent,
      kind: 'navigate',
      target: { url: artifactUrl },
    });
    if (!settledOrStop(opened, steps)) return { ok: false, artifact: null };
    page = await session.observe();
  }
  const exported = await session.act(page, {
    actionId: `${runId}-artifact-download`,
    authorizedIntent: intent,
    kind: 'download',
    target: findElement(page, (element) => element.tag === 'a' && element.text === artifactLinkText, `link ${artifactLinkText}`),
  });
  steps.push(exported);
  return {
    ok: exported.outcome === OUTCOMES.COMPLETED,
    status: exported.outcome ?? exported.dispatchStatus,
    artifact: exported.outcome === OUTCOMES.COMPLETED ? exported.evidence.effect : null,
  };
}

/**
 * @param {ReturnType<import('./owner-session.js').createOwnerSession>} session
 * @param {{
 *   runId: string,
 *   intent: string,
 *   incidentUrl: string,
 *   signals?: string[],
 *   maxRunbooks?: number,
 *   dispositionFields: Record<string, string>,
 *   preconditions?: object[],
 *   completedWhen: object[],
 *   failedWhen?: object[],
 *   artifactUrl?: string,
 *   artifactLinkText?: string,
 *   externalIdempotencyKey?: string,
 *   resubmissionOf?: string
 * }} task
 */
async function runEngineeringInvestigation(session, task) {
  const {
    runId,
    intent,
    incidentUrl,
    signals = [],
    maxRunbooks = 3,
    dispositionFields,
    preconditions = [],
    completedWhen,
    failedWhen = [],
    artifactUrl = null,
    artifactLinkText = null,
  } = task;
  const steps = [];
  const evidence = [];
  const skipped = [];
  const effectKey = investigationEffectKey(incidentUrl, dispositionFields);
  const lowerSignals = signals.map((signal) => signal.toLowerCase());

  const ensureIncidentPage = async (label) => {
    const current = await session.observe();
    if (current.url === incidentUrl) return current;
    const nav = await session.act(current, {
      actionId: `${runId}-incident-${label}`,
      authorizedIntent: intent,
      kind: 'navigate',
      target: { url: incidentUrl },
    });
    if (!settledOrStop(nav, steps)) return null;
    return session.observe();
  };

  const initial = await ensureIncidentPage('open');
  if (!initial) return { status: 'stopped', effectKey, evidence, skipped, artifact: null, steps };
  evidence.push({
    kind: 'incident',
    url: initial.url,
    title: initial.title,
    sha256: sha256Hex(initial.text),
    observationVersion: initial.observationVersion,
    passages: lowerSignals.length > 0
      ? initial.text.split(LINE_BREAK).filter((line) => lowerSignals.some((signal) => line.toLowerCase().includes(signal)))
      : initial.text.split(LINE_BREAK).filter(Boolean),
  });

  if (lowerSignals.length > 0 && maxRunbooks > 0) {
    const links = initial.elements
      .filter((element) => element.tag === 'a' && element.href
        && lowerSignals.some((signal) => element.text.toLowerCase().includes(signal)))
      .slice(0, maxRunbooks)
      .map((element) => ({ href: element.href, text: element.text }));

    for (const [index, link] of links.entries()) {
      const fromIncident = await ensureIncidentPage(`return-${index}`);
      if (!fromIncident) return { status: 'stopped', effectKey, evidence, skipped, artifact: null, steps };
      let opened;
      try {
        opened = await session.act(fromIncident, {
          actionId: `${runId}-runbook-${index}`,
          authorizedIntent: intent,
          kind: 'click',
          target: findElement(fromIncident, (element) => element.href === link.href, `runbook link ${link.href}`),
          completion: { completedWhen: [{ kind: 'url-equals', value: link.href }] },
        });
      } catch (error) {
        if (error.code !== REJECTION_CODES.UNAUTHORIZED_TARGET) throw error;
        skipped.push({ href: link.href, code: error.code });
        continue;
      }
      if (!settledOrStop(opened, steps)) return { status: 'stopped', effectKey, evidence, skipped, artifact: null, steps };
      const runbook = await session.observe();
      evidence.push({
        kind: 'runbook',
        url: runbook.url,
        title: runbook.title,
        sha256: sha256Hex(runbook.text),
        observationVersion: runbook.observationVersion,
        passages: runbook.text.split(LINE_BREAK)
          .filter((line) => lowerSignals.some((signal) => line.toLowerCase().includes(signal))),
      });
    }
  }

  const beforeFill = await ensureIncidentPage('prepare-disposition');
  if (!beforeFill) return { status: 'stopped', effectKey, evidence, skipped, artifact: null, steps };

  const fieldSelectors = {};
  for (const [name, value] of Object.entries(dispositionFields)) {
    const current = await session.observe();
    const target = findElement(current, (element) => element.attributes.some(([key, val]) => key === 'name'
      && val === name), `disposition field ${name}`);
    fieldSelectors[name] = target.selector;
    const filled = await session.act(current, {
      actionId: `${runId}-fill-${name}`,
      authorizedIntent: intent,
      kind: 'fill',
      target,
      params: { value },
    });
    if (!settledOrStop(filled, steps)) {
      return { status: 'stopped', effectKey, evidence, skipped, artifact: null, steps };
    }
  }

  const ready = await session.observe();
  const effect = { external: true, effectKey };
  if (task.externalIdempotencyKey) effect.externalIdempotencyKey = task.externalIdempotencyKey;
  const submission = await session.act(ready, {
    actionId: `${runId}-submit`,
    authorizedIntent: intent,
    kind: 'submit',
    target: findElement(ready, (element) => element.formAction && element.attributes.some(([key, val]) => key === 'type'
      && val === 'submit'), 'disposition submit control'),
    preconditions: [
      ...Object.entries(dispositionFields).map(([name, value]) => ({
        kind: 'input-value-equals',
        selector: fieldSelectors[name],
        value,
      })),
      ...preconditions,
    ],
    effect,
    completion: { completedWhen, failedWhen },
    resubmissionOf: task.resubmissionOf,
  });
  steps.push(submission);
  if (submission.outcome !== OUTCOMES.COMPLETED) {
    return {
      status: submission.outcome ?? submission.dispatchStatus,
      effectKey,
      evidence,
      skipped,
      submission,
      artifact: null,
      steps,
    };
  }

  const bundle = await exportBundle(session, { runId, intent, artifactUrl, artifactLinkText }, steps);
  return {
    status: bundle.ok ? OUTCOMES.COMPLETED : (bundle.status ?? 'stopped'),
    effectKey,
    evidence,
    skipped,
    submission,
    artifact: bundle.artifact,
    steps,
  };
}

/**
 * Finish an engineering investigation after an interruption. Reconciles an uncertain disposition
 * against the incident audit log before deciding whether to finish artifact export, resubmit once
 * with explicit provenance, or stop for human review.
 * @param {ReturnType<import('./owner-session.js').createOwnerSession>} session
 * @param {Parameters<typeof runEngineeringInvestigation>[1] & {
 *   auditUrl: string,
 *   auditSelector: string,
 *   auditEntry?: string
 * }} task
 */
async function recoverEngineeringInvestigation(session, task) {
  const effectKey = investigationEffectKey(task.incidentUrl, task.dispositionFields);
  const outstanding = await session.outstanding();
  const latest = outstanding.filter((action) => action.effectKey === effectKey && action.kind === 'submit').at(-1);
  const priorDownload = task.artifactLinkText
    ? outstanding.find((action) => action.kind === 'download' && action.outcome === OUTCOMES.COMPLETED)
    : null;

  const completeBundle = async (recovered, steps = []) => {
    if (!task.artifactLinkText) return { status: OUTCOMES.COMPLETED, effectKey, artifact: null, recovered, steps };
    if (priorDownload) {
      return { status: OUTCOMES.COMPLETED, effectKey, artifact: priorDownload.evidence.effect, recovered, steps };
    }
    const bundle = await exportBundle(session, {
      runId: `${task.runId}-resume`,
      intent: task.intent,
      artifactUrl: task.artifactUrl ?? null,
      artifactLinkText: task.artifactLinkText,
    }, steps);
    return {
      status: bundle.ok ? OUTCOMES.COMPLETED : (bundle.status ?? 'stopped'),
      effectKey,
      artifact: bundle.artifact,
      recovered,
      steps,
    };
  };

  const resubmit = async (resubmissionOf, recovered) => ({
    ...await runEngineeringInvestigation(session, { ...task, runId: `${task.runId}-resubmit`, resubmissionOf }),
    recovered,
  });

  if (!latest) {
    try {
      return await runEngineeringInvestigation(session, task);
    } catch (error) {
      if (error.code === REJECTION_CODES.EFFECT_ALREADY_COMPLETED) return completeBundle('already-completed');
      throw error;
    }
  }
  if (latest.outcome === OUTCOMES.COMPLETED) return completeBundle('recorded-outcome');
  if (latest.outcome === OUTCOMES.FAILED) return { status: OUTCOMES.FAILED, effectKey, artifact: null, recovered: 'recorded-outcome', steps: [] };
  if (latest.dispatchStatus === ACTION_STATUS.NEVER_DISPATCHED) return resubmit(latest.actionId, 'resubmitted-never-dispatched');
  if (!latest.isUncertain) {
    return latest.reconciliation.result === 'effect-present'
      ? completeBundle('earlier-reconciliation')
      : resubmit(latest.actionId, 'resubmitted-after-earlier-reconciliation');
  }

  const steps = [];
  const auditPage = await session.act(await session.observe(), {
    actionId: `${task.runId}-open-audit`,
    authorizedIntent: task.intent,
    kind: 'navigate',
    target: { url: task.auditUrl },
  });
  steps.push(auditPage);
  if (auditPage.outcome !== OUTCOMES.COMPLETED) return { status: 'stopped', effectKey, artifact: null, steps };

  const expectedEntry = task.auditEntry ?? Object.values(task.dispositionFields).join(' ');
  const reconciled = await session.reconcile({
    actionId: latest.actionId,
    method: 'application-state',
    effectPresentWhen: [{ kind: 'element-text-includes', selector: task.auditSelector, value: expectedEntry }],
    effectAbsentWhen: [{ kind: 'element-text-excludes', selector: task.auditSelector, value: expectedEntry }],
  });
  const result = reconciled.reconciliation.result;
  if (result === 'effect-present') return completeBundle('application-state', steps);
  if (result === 'effect-absent') return resubmit(latest.actionId, 'resubmitted-after-absence');
  return { status: OUTCOMES.UNKNOWN, effectKey, artifact: null, recovered: 'human-review-needed', steps };
}

export { investigationEffectKey, recoverEngineeringInvestigation, runEngineeringInvestigation };
