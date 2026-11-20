// What a returning operator needs before trusting an investigation again: which saved sources
// changed, which conclusions rest on them and need rechecking, what still holds, which
// explanations were already rejected, and the next useful step. Pure: it reads the investigation
// records and the latest recorded source check; reading files and pages belongs to the controller.
const CLIP = 240, EXCERPT = 600;
// The brief travels in every handoff, so each list is bounded and reports how much it left out.
// What needs rechecking is listed first and most fully; what still holds is mostly a count.
const LIMITS = Object.freeze({ changedSources: 12, uncheckedSources: 12, needsRecheck: 20, stillValid: 12, hypotheses: 12 });
const bounded = (items, limit) => ({ shown: items.slice(0, limit), omitted: Math.max(0, items.length - limit) });
const clip = (text, size = CLIP) => (typeof text === 'string' && text.length > size ? `${text.slice(0, size)}…` : text ?? '');
const label = artifact => artifact.source?.kind === 'repository' ? artifact.source.path : artifact.source?.url ?? artifact.id;

/** Where two versions of a text differ, as line ranges with bounded excerpts. Not a full diff. */
export function describeChange(before, after) {
  const a = String(before ?? '').split('\n'), b = String(after ?? '').split('\n');
  let head = 0;
  while (head < a.length && head < b.length && a[head] === b[head]) head += 1;
  let tail = 0;
  while (tail < a.length - head && tail < b.length - head && a[a.length - 1 - tail] === b[b.length - 1 - tail]) tail += 1;
  const removed = a.slice(head, a.length - tail), added = b.slice(head, b.length - tail);
  return { beforeLines: a.length, afterLines: b.length, firstChangedLine: head + 1,
    removedLines: removed.length, addedLines: added.length,
    removedExcerpt: clip(removed.join('\n'), EXCERPT), addedExcerpt: clip(added.join('\n'), EXCERPT) };
}

/** Evidence a record rests on, followed through every intermediate record. */
function roots(project, artifact, seen = new Set()) {
  const found = [];
  for (const id of artifact.dependsOn ?? []) {
    const parent = project.artifacts[id];
    if (!parent || seen.has(id)) continue;
    seen.add(id);
    if (parent.kind === 'evidence') found.push(parent); else found.push(...roots(project, parent, seen));
  }
  return found;
}

/**
 * @param project  investigation as saved
 * @param options.unresolvedActions  count of browser actions whose outcome is still unknown
 */
export function validityBrief(project, { unresolvedActions = 0 } = {}) {
  const artifacts = Object.values(project.artifacts);
  const check = project.activity.findLast(event => event.event === 'sources-checked') ?? null;
  const changed = new Map((check?.changed ?? []).map(entry => [entry.artifactId, entry]));
  const reasoning = artifacts.filter(value => value.kind !== 'evidence');
  const needsRecheck = [], stillValid = [];
  for (const artifact of reasoning) {
    const sources = roots(project, artifact);
    // A source that could not be re-read (deleted, unreadable) leaves its saved copy in place, so the
    // store cannot flag its dependents; they are flagged here.
    const lost = sources.filter(source => changed.get(source.id)?.missing);
    const stale = artifact.status === 'needs-review' || lost.length > 0;
    const entry = { id: artifact.id, kind: artifact.kind, revision: artifact.revision, text: clip(artifact.text, stale ? CLIP : 80),
      ...(artifact.disposition ? { disposition: artifact.disposition.state } : {}) };
    if (!stale) { if (artifact.disposition?.state !== 'rejected') stillValid.push(entry); continue; }
    // Name the cause: a parent recorded at an older revision, a parent itself under review, or a lost source.
    const because = (artifact.dependsOn ?? []).flatMap(id => {
      const parent = project.artifacts[id];
      if (!parent) return [{ id, reason: 'no longer exists' }];
      if (parent.revision !== artifact.dependencyRevisions?.[id]) {
        return [{ id, what: parent.kind === 'evidence' ? label(parent) : clip(parent.text, 80), reason: parent.kind === 'evidence' ? 'source changed since this was recorded' : 'was revised since this was recorded',
          recordedAtRevision: artifact.dependencyRevisions?.[id] ?? null, currentRevision: parent.revision }];
      }
      return parent.status === 'needs-review' ? [{ id, what: clip(parent.text, 80), reason: 'itself needs rechecking' }] : [];
    });
    needsRecheck.push({ ...entry, because: [...because, ...lost.map(source => ({ id: source.id, what: label(source), reason: 'source could not be re-read' }))] });
  }
  const hypotheses = reasoning.filter(value => value.kind === 'hypothesis');
  const openQuestions = reasoning.filter(value => value.kind === 'question' && value.status === 'current');
  const openHypotheses = hypotheses.filter(value => value.disposition?.state === 'open');
  const changedSources = [...changed.values()].map(entry => ({ ...entry,
    affects: needsRecheck.filter(item => roots(project, project.artifacts[item.id]).some(source => source.id === entry.artifactId)).map(item => item.id) }));
  const nextAction = unresolvedActions > 0 ? `Establish the ${unresolvedActions} browser action(s) with an unknown outcome before anything else.`
    : needsRecheck.length ? `Recheck ${needsRecheck.length} record(s) against the changed sources: confirm each still holds and record it again, or correct it. Start with ${needsRecheck[0].kind} ${needsRecheck[0].id}.`
      : openHypotheses.length ? `Test the open hypothesis ${openHypotheses[0].id}: find evidence that supports or rejects it.`
        : openQuestions.length ? `Answer the open question ${openQuestions[0].id}.`
          : check ? 'Nothing recorded needs rechecking. Continue the task or finish.' : 'Sources have not been checked against their current state; check them before relying on saved conclusions.';
  const rejected = hypotheses.filter(value => value.disposition?.state === 'rejected')
    .map(value => ({ id: value.id, text: clip(value.text), reason: clip(value.disposition.reason), dependsOn: value.dependsOn ?? [] }));
  const lists = { changedSources: bounded(changedSources, LIMITS.changedSources), uncheckedSources: bounded(check?.unchecked ?? [], LIMITS.uncheckedSources),
    needsRecheck: bounded(needsRecheck, LIMITS.needsRecheck), stillValid: bounded(stillValid, LIMITS.stillValid),
    rejectedHypotheses: bounded(rejected, LIMITS.hypotheses), openHypotheses: bounded(openHypotheses.map(value => ({ id: value.id, text: clip(value.text) })), LIMITS.hypotheses) };
  const omitted = Object.fromEntries(Object.entries(lists).filter(([, list]) => list.omitted > 0).map(([name, list]) => [name, list.omitted]));
  return {
    sourcesCheckedAt: check?.at ?? null, unchangedSourceCount: check?.unchangedCount ?? null,
    counts: { changedSources: changedSources.length, needsRecheck: needsRecheck.length, stillValid: stillValid.length, rejectedHypotheses: rejected.length, openHypotheses: openHypotheses.length },
    ...Object.fromEntries(Object.entries(lists).map(([name, list]) => [name, list.shown])),
    // Entries left out of the lists above; artifact_list and artifact_read reach every record.
    ...(Object.keys(omitted).length ? { omitted } : {}),
    nextAction,
  };
}

/**
 * Why a finish should be returned to the agent: saved records are still marked as needing review.
 * Returns the message to give the agent, or null when nothing is outstanding.
 */
export function unfinishedRecords(project, { limit = 8 } = {}) {
  const stale = Object.values(project.artifacts).filter(value => value.kind !== 'evidence' && value.status === 'needs-review');
  if (!stale.length) return null;
  const listed = stale.slice(0, limit).map(value => `${value.id} (${value.kind}, revision ${value.revision})`).join('; ');
  return `${stale.length} saved record(s) still need rechecking because a source they rest on changed: ${listed}${stale.length > limit ? '; and more' : ''}. `
    + 'Check each against the current source, then save it again with the record tool, passing its id and expectedRevision and correcting the text if it no longer holds. '
    + 'The record tool is available through your reply. Finish after that; a second finish is accepted as it stands.';
}
