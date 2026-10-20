'use strict';
// Reproduce the mechanical arm from the public, hash-bound baseline sources.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {TextDecoder} = require('util');
const {rewrite} = require('./rewrite.cjs');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const destination = process.argv[2];
if (!destination) throw new Error('Usage: node generate.cjs NEW_OUTPUT_DIRECTORY');
const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, 'source_manifest.json'), 'utf8'));
const pending = [];
for (const key of Object.keys(manifest.source_hashes).filter(key => key.endsWith('/baseline')).sort()) {
  const id = key.split('/')[0];
  const raw = fs.readFileSync(path.join(__dirname, '../sources/normalized', id + '.js'));
  if (hash(raw) !== manifest.source_hashes[key]) throw new Error('Input drift: ' + id);
  const text = new TextDecoder('utf-8', {fatal: true, ignoreBOM: true}).decode(raw);
  if (!Buffer.from(text).equals(raw)) throw new Error('UTF-8 roundtrip failed');
  const result = rewrite(text);
  if (hash(result.source) !== manifest.source_hashes[id + '/recomposed']) throw new Error('Output drift: ' + id);
  pending.push({id, ...result});
}
fs.mkdirSync(destination);
for (const result of pending) fs.writeFileSync(path.join(destination, result.id + '.js'), result.source, {flag: 'wx'});
const metadata = pending.map(({source, ...rest}) => rest);
fs.writeFileSync(path.join(destination, 'transformations.json'), JSON.stringify(metadata, null, 2) + '\n');
console.log(JSON.stringify({programs: pending.length, rewritten: pending.filter(x => x.status === 'rewritten').length}));
