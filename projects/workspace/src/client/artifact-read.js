// Read saved investigation bytes, never a live page or an arbitrary filesystem path.
import { sha256Hex } from '../journal.js';

export const MAX_ARTIFACT_READ_CHARS = 6000;
const MAX_FIND_CHARS = 200, MAX_MATCH_OFFSETS = 20, MAX_DEFINITIONS = 40, MAX_NAME_CHARS = 60;

// Named places in a saved source: functions, classes, methods, bound arrow functions, Python
// definitions and Markdown headings. A cheap line scan, not a parser; it exists so that what lies
// beyond the part of a long file shown by default can be seen and jumped to.
const DEFINITIONS = [
  /^[ \t]*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\*?\s+([A-Za-z_$][\w$]*)/,
  /^[ \t]*(?:export\s+)?(?:default\s+)?class\s+([A-Za-z_$][\w$]*)/,
  /^[ \t]*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>/,
  /^[ \t]+(?:static\s+)?(?:async\s+)?\*?(#?[A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{\s*$/,
  /^[ \t]*(?:async\s+)?def\s+([A-Za-z_]\w*)/,
  /^(#{1,3}\s+\S.*)$/,
];
const NOT_DEFINITIONS = new Set(['if', 'for', 'while', 'switch', 'catch', 'function', 'return']);
/** Named places at or after `from`, in order, bounded. `more` counts what the bound left out. */
export function definitionsIn(text, from = 0) {
  const found = [];
  let offset = 0, more = 0;
  for (const line of String(text ?? '').split('\n')) {
    if (offset >= from) {
      const name = DEFINITIONS.map(pattern => pattern.exec(line)?.[1]).find(Boolean);
      if (name && !NOT_DEFINITIONS.has(name)) { if (found.length < MAX_DEFINITIONS) found.push({ name: name.trim().slice(0, MAX_NAME_CHARS), offset }); else more += 1; }
    }
    offset += line.length + 1;
  }
  return { definitions: found, more };
}

export function readArtifact(project, { artifactId, expectedRevision, offset = 0, maxChars = MAX_ARTIFACT_READ_CHARS, field = null, find = null }, visibleArtifacts) {
  if (!(visibleArtifacts instanceof Set) || !visibleArtifacts.has(artifactId)) throw Error('Source record was not shared with this task');
  const artifact = Object.hasOwn(project.artifacts, artifactId) ? project.artifacts[artifactId] : null;
  if (!artifact) throw Error('Unknown source record');
  if (!Number.isSafeInteger(expectedRevision) || expectedRevision !== artifact.revision) throw Error('Artifact changed; read its current revision before requesting saved bytes');
  if (!Number.isSafeInteger(offset) || offset < 0 || !Number.isSafeInteger(maxChars)
    || maxChars < 1 || maxChars > MAX_ARTIFACT_READ_CHARS) throw Error('Use a nonnegative character offset and a bounded maxChars');
  field ??= typeof artifact.source?.content === 'string' ? 'source' : 'text';
  if (!['source', 'text'].includes(field)) throw Error('Read the source or text field');
  const text = field === 'source' ? artifact.source?.content : artifact.text;
  if (typeof text !== 'string') throw Error('The requested record field has no saved text');
  if (offset > text.length) throw Error('Character offset exceeds the saved record');
  // `find` jumps to literal text instead of paging to it: the slice starts shortly before the first
  // match at or after `offset`, and every match in the field is listed so the rest can be visited.
  let matches = null;
  if (find !== null) {
    if (typeof find !== 'string' || !find || find.length > MAX_FIND_CHARS) throw Error('Find takes literal text of 1 to 200 characters');
    const offsets = [], needle = find.toLowerCase(), haystack = text.toLowerCase();
    let total = 0;
    for (let at = haystack.indexOf(needle); at !== -1; at = haystack.indexOf(needle, at + 1)) { total += 1; if (offsets.length < MAX_MATCH_OFFSETS) offsets.push(at); }
    const next = offsets.find(at => at >= offset) ?? null;
    matches = { find, total, offsets, shownFrom: next, note: total ? (next === null ? 'No match at or after this offset; earlier matches are listed.' : 'Case-insensitive literal matches in this field.')
      : 'No match in this field of this record.' };
    if (next === null) return { artifactId, revision: artifact.revision, kind: artifact.kind, status: artifact.status,
      classification: 'saved record excerpt; no new observation or permission', field, totalChars: text.length, matches, content: '' };
    offset = Math.max(0, next - Math.floor(maxChars / 4));
  }
  const end = Math.min(text.length, offset + maxChars);
  const content = text.slice(offset, end);
  return { artifactId, revision: artifact.revision, kind: artifact.kind, status: artifact.status,
    classification: 'saved record excerpt; no new observation or permission',
    field, sourceSha256: field === 'source' ? artifact.source.sha256 : null, contentHash: artifact.contentHash,
    offsetUnit: 'UTF-16 code units', offset, end, totalChars: text.length, nextOffset: end < text.length ? end : null,
    content, sliceSha256: sha256Hex(content), ...(matches ? { matches } : {}) };
}
