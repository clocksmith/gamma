import { validityBrief } from './validity.js';
// Bounded continuation view of the complete journal and service action records.
// This summary grants no authority and never settles an uncertain action.
const LIMITS = Object.freeze({ sessions: 8, tried: 40, human: 12, unresolvedActions: 20, openQuestions: 12, needsReview: 20 });
const MAX_TEXT = 400;
const SIGN_IN = 'Site sign-ins may be lost: observe each site before relying on a session, and ask_human to sign in again if it is gone.';
const RELEASE_NOTES = Object.freeze({
  forced: `The browser was ended at the last shutdown. ${SIGN_IN}`,
  'already-exited': `The browser had already exited at the last shutdown without closing cleanly. ${SIGN_IN}`,
  unresolved: `A browser from the last shutdown could not be shown to have exited and may still be running on this profile; ask_human to check before relying on the pages. ${SIGN_IN}`,
});
const clip = value => {
  const text = typeof value === 'string' ? value : JSON.stringify(value ?? null);
  return text.length > MAX_TEXT ? `${text.slice(0, MAX_TEXT)}…` : text;
};
function bounded(value) {
  const text = JSON.stringify(value ?? null);
  return text.length <= MAX_TEXT ? value : { excerpt: clip(text), truncated: true, totalCharacters: text.length };
}
function summarizeOutput(output) {
  if (output == null) return null;
  if (output.id && output.kind) return { artifactId: output.id, kind: output.kind };
  if (output.actionId) return { actionId: output.actionId, kind: output.kind ?? null, outcome: output.outcome ?? null,
    basis: bounded(output.outcomeBasis ?? null), isUncertain: !!output.isUncertain };
  if (output.error) return { error: clip(output.error) };
  return { summary: clip(output) };
}

/** Cursors select older pages; use only the opaque nextCursor returned for that collection. */
export function handoffBrief(project, workspace = null, { cursors = {} } = {}) {
  const sessions = [], human = [], requested = new Map(), pagination = {};
  let current = null, forcedRelease = null;
  // One forward settlement scan: each call is indexed once and updated on result.
  for (let index = 0; index < project.activity.length; index++) {
    const event = project.activity[index], provenance = { seq: event.seq ?? null, activityIndex: index };
    const cursor = String(event.seq ?? `activity:${index}`);
    if (event.event === 'delegated') {
      current = { cursor, event, provenance, ended: null, finishProposal: null }; sessions.push(current);
    } else if (event.event === 'finish' || event.event === 'ask_human') {
      if (current) current.finishProposal = { how: event.event, text: clip(event.text), seq: event.seq ?? null };
    } else if (event.type === 'run-updated' && event.run?.status !== 'running') {
      if (current) current.ended = { how: event.run.status, detail: clip(event.run.detail ?? ''), seq: event.seq ?? null };
    } else if (event.event === 'tool-requested') {
      requested.set(event.callId, { cursor: event.callId, event, provenance, result: null });
    } else if (event.event === 'tool-result' || event.event === 'tool-failed') {
      const call = requested.get(event.callId);
      if (call) call.result = event;
    } else if (event.event === 'human-control' || event.event === 'human-note') {
      human.push({ cursor, event, provenance });
    } else if (event.event === 'browser-released') {
      // Records written before the release kind existed carry only `forced`.
      const release = event.release ?? (event.forced ? 'forced' : 'graceful');
      forcedRelease = release === 'graceful' ? null : { release, seq: event.seq ?? null, at: event.at ?? null,
        ...(event.survivors ? { survivors: event.survivors } : {}) };
    }
  }
  function page(name, entries, summarize) {
    let end = entries.length;
    if (cursors[name] !== undefined && cursors[name] !== null) {
      end = entries.findIndex(entry => entry.cursor === cursors[name]);
      if (end < 0) throw Error(`Unknown or expired ${name} handoff cursor; refresh the handoff.`);
    }
    const start = Math.max(0, end - LIMITS[name]);
    pagination[name] = { total: entries.length, included: end - start, omittedOlder: start,
      omittedNewer: entries.length - end, nextCursor: start > 0 ? entries[start].cursor : null };
    return entries.slice(start, end).map(summarize);
  }
  const unresolved = (workspace?.actions ?? []).filter(action => action.isUncertain);
  const artifacts = Object.values(project.artifacts);
  const result = {
    previousRun: project.run ? { status: project.run.status, detail: clip(project.run.detail ?? ''), turns: project.run.turns } : null,
    sessions: page('sessions', sessions, ({ event, provenance, ended, finishProposal }) => ({ ...provenance,
      task: clip(event.task), startedAt: event.at, actionKinds: bounded(event.actionKinds),
      pageIds: bounded(event.pageIds), origins: bounded(event.origins), ended, finishProposal })),
    tried: page('tried', [...requested.values()].filter(call => call.result || !['finish', 'ask_human'].includes(call.event.tool)),
      ({ event, provenance, result }) => ({ ...provenance, callId: event.callId, requestSeq: event.seq ?? null,
        resultSeq: result?.seq ?? null, tool: event.tool, input: clip(event.input),
        result: result ? result.event === 'tool-failed' ? { error: clip(result.error) } : summarizeOutput(result.output)
          : { interrupted: 'no recorded result; the session ended first' } })),
    human: page('human', human, ({ event, provenance }) => ({ ...provenance, at: event.at,
      event: event.event === 'human-control' ? 'took control' : 'note',
      ...(event.event === 'human-control' ? { outstandingActions: event.outstanding?.length ?? 0 } : { text: clip(event.text) }) })),
    unresolvedActionCount: unresolved.length,
    unresolvedActions: page('unresolvedActions', unresolved.map(action => ({ cursor: action.actionId, action })), ({ action }) => ({
      actionId: action.actionId, pageId: action.pageId, kind: action.kind, target: bounded(action.target),
      effectKey: action.effectKey == null ? null : clip(action.effectKey), completion: bounded(action.completion), outcome: action.outcome,
      basis: bounded(action.outcomeBasis), lastReconciliation: action.reconciliation?.result ?? null,
    })),
    openQuestions: page('openQuestions', artifacts.filter(value => value.kind === 'question' && value.status === 'current')
      .map(value => ({ cursor: value.id, value })), ({ value }) => ({ id: value.id, revision: value.revision, text: clip(value.text) })),
    needsReview: page('needsReview', artifacts.filter(value => value.status === 'needs-review')
      .map(value => ({ cursor: value.id, value })), ({ value }) => value.id),
    // What still holds, what changed underneath it, which explanations were already rejected, and
    // the next useful step. Read this before relying on any saved conclusion.
    validity: validityBrief(project, { unresolvedActions: unresolved.length }),
    pagination,
    // The browser did not close cleanly at the last shutdown. Recorded work is intact; a site session
    // set shortly before may not have reached disk, and an unresolved browser may still be running.
    ...(forcedRelease ? { lastBrowserRelease: { forced: forcedRelease.release === 'forced', ...forcedRelease, note: RELEASE_NOTES[forcedRelease.release] ?? RELEASE_NOTES.forced } } : {}),
    authority: 'The complete investigation journal (seq/callId) and service action records (actionId) remain authoritative; excerpts are summaries. Use handoff_read with pagination[collection].nextCursor to retrieve older entries.',
    guidance: unresolved.length
      ? `${unresolved.length} earlier actions have unknown outcomes, including any omitted from this page. Establish every one with reconcile before a new action; never repeat one unless reconcile returns effect-absent. Page through unresolvedActions with handoff_read as needed.`
      : 'No earlier action has an unknown outcome.',
  };
  return result;
}
