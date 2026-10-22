// Classify sixbit-v1 vocabularies with BITS's macro-entry rule (read-only use of 256one
// public/labs/two-button/macro-entries.js), and count near-whole-program entries: entries
// found in exactly one cohort program and at least half its length. The second measure is
// a post-hoc reporting addition: the BITS rule needs a definition whose closing brace is
// inside the entry, so an entry ending just before a program's last brace is not flagged.
// Usage: node classify_macros.mjs <256one/public/labs/two-button> <run dir>...
import {readFileSync, writeFileSync, readdirSync, existsSync} from 'node:fs';
import {resolve, basename, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const [bits, ...runs] = process.argv.slice(2);
const {macroDefinitions} = await import(resolve(bits, 'macro-entries.js'));
const scale = resolve(here, '../scale-v2/generated');
const ids = new Set(JSON.parse(readFileSync(resolve(here, '../matched80-v1/labels/ids.json'))));
const rows = [];
for (const run of runs) for (const job of readdirSync(run).sort()) {
  const file = resolve(run, job, 'manifest.json');
  if (!existsSync(file)) continue;
  const m = JSON.parse(readFileSync(file, 'utf8'));
  if (!m.vocabulary) continue;
  const texts = JSON.parse(readFileSync(resolve(scale, 'manifest.json'))).rows
    .filter(r => r.variant === m.style && ids.has(r.id)).map(r => readFileSync(resolve(scale, r.file), 'utf8'));
  const macros = [], nearWhole = [];
  for (const text of m.vocabulary) {
    const found = macroDefinitions(text, 'javascript');
    if (found.length) macros.push({bytes: Buffer.byteLength(text), definitions: found.map(d => d.name ? `${d.kind} ${d.name}` : d.kind)});
    const owners = texts.filter(t => t.includes(text));
    if (owners.length === 1 && text.length * 2 >= owners[0].length) nearWhole.push(text.length);
  }
  rows.push({run: basename(run), job, entries: m.vocabulary.length, category: macros.length ? 'macro' : 'primitive',
             macro_entries: macros.length, near_whole_program_entries: nearWhole.length, near_whole_lengths: nearWhole.sort((a, b) => a - b), macros});
}
writeFileSync(resolve(here, 'macro-entries.json'), JSON.stringify({
  schema: 'gamma.sixbit.macro-entries.v1',
  classifier: '256one public/labs/two-button/macro-entries.js macroDefinitions (BITS_PROMOTION.md macro rule)',
  near_whole_program: 'entry occurring in exactly one cohort program, at least half that program long (reporting addition, not part of the freeze)',
  rows}, null, 2) + '\n');
for (const r of rows) console.log(r.run, r.job, r.category, `${r.macro_entries} macro`, `${r.near_whole_program_entries} near-whole`, `of ${r.entries}`);
