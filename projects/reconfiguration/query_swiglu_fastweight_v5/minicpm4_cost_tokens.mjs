// Count expected answer tokens in the locked task format without running inference.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
const [engine, artifact] = process.argv.slice(2);
const moduleAt = path => import(pathToFileURL(resolve(engine, path)).href);
// Doppler logs its level change; reserve stdout for the mapping.
console.log = console.error;
const {setLogLevel} = await moduleAt('src/debug/config.js');
setLogLevel('silent');
const {BundledTokenizer} = await moduleAt('src/inference/tokenizers/bundled.js');
const tokenizer = new BundledTokenizer({vocabSize:73448, deferSpecialTokens:true, addBosToken:false, addEosToken:false});
tokenizer.load(JSON.parse(fs.readFileSync(artifact, 'utf8')));
const codes = JSON.parse(fs.readFileSync(0, 'utf8'));
const marker = 'Item: a noun on the shelf =>';
const prefix = Array.from(tokenizer.encode(marker));
const output = {};
for (const code of codes) {
  const tokens = Array.from(tokenizer.encode(marker + ' ' + code));
  assert.deepEqual(tokens.slice(0,prefix.length), prefix);
  assert.ok(tokens.length > prefix.length);
  output[code] = tokens.length - prefix.length;
}
process.stdout.write(JSON.stringify(output));
