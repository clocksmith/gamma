// Bounded planner views over the complete, explicitly shared evidence store.
import { definitionsIn } from './artifact-read.js';
const RECENT_ARTIFACTS = 8;
const EXCERPT_CHARS = 6000;
const CATALOG_PAGE = 12;
const clip = (text, size) => typeof text === 'string' ? text.slice(0, size) : text;
function sharedArtifacts(project, visibleArtifacts) {
  if (!(visibleArtifacts instanceof Set)) throw Error('Explicit shared-record identities required');
  const modified = new Map();
  for (let index = 0; index < project.activity.length; index++) {
    const event = project.activity[index];
    if (event.type === 'artifact-revised') modified.set(event.artifact.id, index);
  }
  const total = Object.keys(project.artifacts).length;
  return Object.values(project.artifacts).filter(value => visibleArtifacts.has(value.id))
    .map((value, index) => ({ value, order: modified.get(value.id) ?? index - total }))
    .sort((a, b) => b.order - a.order).map(entry => entry.value);
}
function excerpt(artifact) {
  const result = { ...artifact };
  if (typeof artifact.text === 'string' && artifact.text.length > EXCERPT_CHARS) {
    result.text = artifact.text.slice(0, EXCERPT_CHARS);
    result.textTruncated = { shownChars: EXCERPT_CHARS, totalChars: artifact.text.length };
  }
  const content = artifact.source?.content;
  if (typeof content === 'string' && content.length > EXCERPT_CHARS) {
    // Say what the unseen part contains, so a planner knows it is there and can jump to it with
    // artifact_read (offset, or find) instead of concluding from the opening of the file.
    const { definitions, more } = definitionsIn(content, EXCERPT_CHARS);
    result.source = { ...artifact.source, content: content.slice(0, EXCERPT_CHARS),
      contentTruncated: { shownChars: EXCERPT_CHARS, totalChars: content.length,
        ...(definitions.length ? { definitionsBeyondExcerpt: definitions, ...(more ? { moreDefinitions: more } : {}) } : {}) } };
  }
  return result;
}
export function artifactMemory(project, visibleArtifacts) {
  const all = sharedArtifacts(project, visibleArtifacts), recent = all.slice(0, RECENT_ARTIFACTS);
  return { artifacts: Object.fromEntries(recent.map(value => [value.id, excerpt(value)])),
    artifactCatalog: { total: all.length, shown: recent.length, omitted: all.length - recent.length,
      guidance: 'Use artifact_list to search or page through all shared records, then artifact_read for saved bytes at the displayed revision. Omitted records remain stored.' } };
}
export function listArtifacts(project, { after = null, query = '', kind = null, status = null } = {}, visibleArtifacts) {
  if (typeof query !== 'string' || query.length > 200 || (after !== null && typeof after !== 'string')
    || (kind !== null && !['evidence', 'assumption', 'finding', 'decision', 'question'].includes(kind))
    || (status !== null && !['current', 'needs-review'].includes(status))) throw Error('Invalid artifact catalog query');
  // Literal, case-insensitive search; indices stay in the original UTF-16 text.
  const pattern = query ? new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'iu') : null;
  const matches = sharedArtifacts(project, visibleArtifacts).filter(value => (!kind || value.kind === kind)
    && (!status || value.status === status) && (!pattern || [value.text, value.source?.content, value.source?.path, value.source?.url]
      .some(text => typeof text === 'string' && pattern.test(text))));
  const cursor = after === null ? -1 : matches.findIndex(value => value.id === after);
  if (after !== null && cursor < 0) throw Error('Artifact catalog changed or cursor is invalid; refresh the query');
  const start = cursor + 1, selected = matches.slice(start, start + CATALOG_PAGE);
  const matchLocation = value => {
    if (!pattern) return null;
    for (const [field, text] of [['source', value.source?.content], ['text', value.text]]) {
      const match = typeof text === 'string' ? pattern.exec(text) : null;
      if (match) return { field, offset: match.index, length: match[0].length };
    }
    return null;
  };
  return { total: matches.length, offset: start,
    nextCursor: start + selected.length < matches.length ? selected.at(-1).id : null,
    entries: selected.map(value => ({ id: value.id, revision: value.revision, kind: value.kind, status: value.status,
      text: clip(value.text, 400), textTruncated: typeof value.text === 'string' && value.text.length > 400,
      match: matchLocation(value),
      source: value.source ? { kind: value.source.kind, path: clip(value.source.path, 400), url: clip(value.source.url, 400),
        sha256: value.source.sha256, totalChars: value.source.content?.length ?? 0 } : null })) };
}
