// Classify dictionaries with the BITS macro rule (256one macro-entries.js, read-only).
//   node macros.mjs <256one/public/labs/two-button> dictionaries.json  ->  {"<name>": number of macro entries}
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
const [bits, file] = process.argv.slice(2);
const { macroDefinitions } = await import(resolve(bits, 'macro-entries.js'));
const dicts = JSON.parse(readFileSync(file, 'utf8')), out = {};
for (const [name, vocab] of Object.entries(dicts)) out[name] = vocab.filter(t => macroDefinitions(t, 'javascript').length).length;
process.stdout.write(JSON.stringify(out));
