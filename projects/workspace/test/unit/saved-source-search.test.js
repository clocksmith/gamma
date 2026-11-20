// A long saved source shows only its opening. The planner is told what the unseen part contains and
// can jump to literal text, so a conclusion is not drawn from the first 6,000 characters of a file.
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { definitionsIn, readArtifact } from '../../src/client/artifact-read.js';
import { artifactMemory } from '../../src/client/artifact-memory.js';
import { PLANNER_TOOLS } from '../../src/client/planner.js';
import { sha256Hex } from '../../src/journal.js';

const filler = Array.from({ length: 160 }, (_, index) => `  const line${index} = ${index}; // padding so the file is long`).join('\n');
const source = `import { x } from './x.js';\nexport function open(options) {\n${filler}\n}\n`
  + `class Launcher {\n  async launch(progress) {\n    return progress;\n  }\n}\n`
  + `async function closeOrKill(timeout) {\n  await Promise.race([gracefullyClose(), deadline(timeout)]);\n}\n`
  + `export const closeAll = async () => closeOrKill(30000);\ndef helper(value):\n    return value\n# Shutdown\n## Deadlines\n`
  + `  if (ready) {\n  for (const item of items) {\n`;
const evidence = { id: 'launcher', kind: 'evidence', status: 'current', revision: 3, text: 'Repository evidence: lib/launcher.js', dependsOn: [],
  contentHash: 'c'.repeat(64), source: { kind: 'repository', path: 'lib/launcher.js', content: source, sha256: sha256Hex(source) } };
const project = { artifacts: { launcher: evidence }, activity: [] }, visible = new Set(['launcher']);
assert.ok(source.length > 6000 && source.indexOf('closeOrKill') > 6000, 'the deciding code lies beyond the default excerpt');

// The excerpt names what the unseen part contains, with offsets that land on it.
const shown = artifactMemory(project, visible).artifacts.launcher.source;
assert.equal(shown.content.length, 6000);
const beyond = shown.contentTruncated.definitionsBeyondExcerpt;
assert.deepEqual(beyond.map(entry => entry.name), ['Launcher', 'launch', 'closeOrKill', 'closeAll', 'helper', '# Shutdown', '## Deadlines']);
for (const entry of beyond) assert.ok(source.slice(entry.offset).split('\n')[0].includes(entry.name.replace(/^#+\s*/, '')), `${entry.name} is at its offset`);
assert.ok(!beyond.some(entry => ['if', 'for'].includes(entry.name)), 'control flow is not a definition');
assert.equal(definitionsIn(source, 0).definitions[0].name, 'open');
// A short source is shown whole and carries no outline.
const short = { ...evidence, id: 'short', source: { ...evidence.source, content: 'export function a() {}\n', sha256: sha256Hex('export function a() {}\n') } };
assert.equal(artifactMemory({ artifacts: { short }, activity: [] }, new Set(['short'])).artifacts.short.source.contentTruncated, undefined);
// The outline is bounded however many definitions a file has.
const many = Array.from({ length: 300 }, (_, index) => `function f${index}() {}`).join('\n');
assert.deepEqual([definitionsIn(many).definitions.length, definitionsIn(many).more], [40, 260]);

// find jumps to the text: the slice starts shortly before the first match and lists every match.
const jump = readArtifact(project, { artifactId: 'launcher', expectedRevision: 3, find: 'CLOSEORKILL' }, visible);
const first = source.indexOf('closeOrKill');
assert.equal(jump.matches.total, 2);
assert.deepEqual(jump.matches.offsets, [first, source.indexOf('closeOrKill', first + 1)]);
assert.equal(jump.matches.shownFrom, first);
assert.ok(jump.offset <= first && first < jump.end && jump.content.includes('async function closeOrKill(timeout)'));
assert.equal(jump.sliceSha256, sha256Hex(jump.content));
// From a later offset it moves to the next match; past the last one it says so and returns nothing.
assert.equal(readArtifact(project, { artifactId: 'launcher', expectedRevision: 3, find: 'closeOrKill', offset: first + 1 }, visible).matches.shownFrom, jump.matches.offsets[1]);
const past = readArtifact(project, { artifactId: 'launcher', expectedRevision: 3, find: 'closeOrKill', offset: source.length - 5 }, visible);
assert.deepEqual([past.content, past.matches.shownFrom, past.matches.total], ['', null, 2]);
const none = readArtifact(project, { artifactId: 'launcher', expectedRevision: 3, find: 'no such text' }, visible);
assert.deepEqual([none.content, none.matches.total], ['', 0]);
assert.match(none.matches.note, /No match in this field/);
// The same guards as an ordinary read still apply.
assert.throws(() => readArtifact(project, { artifactId: 'launcher', expectedRevision: 2, find: 'x' }, visible), /Artifact changed/);
assert.throws(() => readArtifact(project, { artifactId: 'launcher', expectedRevision: 3, find: 'x' }, new Set()), /not shared/);
assert.throws(() => readArtifact(project, { artifactId: 'launcher', expectedRevision: 3, find: '' }, visible), /literal text/);
assert.throws(() => readArtifact(project, { artifactId: 'launcher', expectedRevision: 3, find: 'y'.repeat(201) }, visible), /literal text/);
assert.equal(readArtifact(project, { artifactId: 'launcher', expectedRevision: 3 }, visible).matches, undefined, 'an ordinary read is unchanged');
assert.match(PLANNER_TOOLS.artifact_read, /pass find/);

// The case this was built for: the installed Playwright launcher, whose 30 s close deadline sits
// beyond the excerpt an agent sees by default.
const real = new URL('../../node_modules/playwright-core/lib/server/browserType.js', import.meta.url);
if (existsSync(real)) {
  const content = readFileSync(real, 'utf8');
  const saved = { ...evidence, id: 'real', revision: 1, source: { kind: 'repository', path: 'lib/server/browserType.js', content, sha256: sha256Hex(content) } };
  const view = artifactMemory({ artifacts: { real: saved }, activity: [] }, new Set(['real'])).artifacts.real.source;
  assert.ok(!view.content.includes('closeOrKill'), 'the deadline is not in the default excerpt');
  assert.ok(view.contentTruncated.definitionsBeyondExcerpt.some(entry => entry.name === 'closeOrKill'), 'but the excerpt says it exists');
  const found = readArtifact({ artifacts: { real: saved }, activity: [] }, { artifactId: 'real', expectedRevision: 1, find: 'DEFAULT_PLAYWRIGHT_TIMEOUT' }, new Set(['real']));
  assert.ok(found.matches.total >= 1 && /closeOrKill\(/.test(found.content));
}
console.log('ok: long saved sources name what lies beyond the excerpt, find jumps to literal text and lists matches, guards unchanged');
