// Fawn workspace — artifact export workflow adapter
//
// Task logic only: opens an export page and downloads the artifact a named link produces.

import { OUTCOMES } from '../state.js';
import { findElement } from './owner-session.js';

/**
 * @param {ReturnType<import('./owner-session.js').createOwnerSession>} session
 * @param {{runId: string, intent: string, exportUrl: string, linkText: string}} task
 */
async function runArtifactExport(session, { runId, intent, exportUrl, linkText }) {
  const steps = [];
  const opened = await session.act(await session.observe(), {
    actionId: `${runId}-open`,
    authorizedIntent: intent,
    kind: 'navigate',
    target: { url: exportUrl },
  });
  steps.push(opened);
  if (opened.outcome !== OUTCOMES.COMPLETED) return { status: 'stopped', steps };
  const page = await session.observe();
  const exported = await session.act(page, {
    actionId: `${runId}-download`,
    authorizedIntent: intent,
    kind: 'download',
    target: findElement(page, (element) => element.tag === 'a' && element.text === linkText, `link ${linkText}`),
  });
  steps.push(exported);
  return {
    status: exported.outcome ?? exported.dispatchStatus,
    artifact: exported.outcome === OUTCOMES.COMPLETED ? exported.evidence.effect : null,
    steps,
  };
}

/**
 * Finish an export task after an interruption. A download the service already recorded as
 * completed is reused; otherwise the export runs again under a fresh run identity, since action
 * ids are never reused and a download is not an external effect.
 * @param {ReturnType<import('./owner-session.js').createOwnerSession>} session
 * @param {Parameters<typeof runArtifactExport>[1]} task
 */
async function recoverArtifactExport(session, task) {
  const downloadId = `${task.runId}-download`;
  const prior = (await session.outstanding()).find((action) => action.actionId === downloadId);
  if (prior?.outcome === OUTCOMES.COMPLETED) {
    return { status: OUTCOMES.COMPLETED, artifact: prior.evidence.effect, recovered: 'recorded-outcome', steps: [] };
  }
  return { ...await runArtifactExport(session, { ...task, runId: `${task.runId}-resume` }), recovered: 'rerun' };
}

export { recoverArtifactExport, runArtifactExport };
