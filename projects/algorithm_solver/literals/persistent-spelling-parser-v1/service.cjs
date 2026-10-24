// Sequential supplied-input service; no filesystem/corpus/source execution.
'use strict';
const logic = require('./logic.cjs');
const REQUEST_LIMIT = 4 * 1024 * 1024, RESPONSE_LIMIT = 16 * 1024 * 1024;
let pending = Buffer.alloc(0), expected = 1;
async function reply(value) {
  const bytes = Buffer.from(JSON.stringify(value)+'\n', 'utf8');
  if (bytes.length > RESPONSE_LIMIT) throw new logic.ParserFailure('RESPONSE_LIMIT');
  await new Promise((resolve,reject) => process.stdout.write(bytes, error => error ? reject(error) : resolve()));
}
async function fail(id, code) {
  try { await reply({id, ok:false, error:code}); } finally { process.exit(1); }
}
async function request(line) {
  let value;
  try { value = JSON.parse(line.toString('utf8')); }
  catch (_) { return fail(null, 'REQUEST_SCHEMA'); }
  if (!value || Array.isArray(value) || Object.keys(value).sort().join(',') !== 'id,texts' ||
      !Number.isSafeInteger(value.id) || value.id !== expected ||
      !value.texts || Array.isArray(value.texts) || typeof value.texts !== 'object' ||
      Object.values(value.texts).some(x => typeof x !== 'string')) return fail(value?.id ?? null, 'REQUEST_SCHEMA');
  try {
    const bodies = logic.bodies(value.texts);
    await reply({id:value.id, ok:true, bodies});
    expected++;
  } catch (error) {
    await fail(value.id, error instanceof logic.ParserFailure ? error.code : 'INTERNAL_ERROR');
  }
}
async function main() {
 for await (const chunk of process.stdin) {
  // A valid client has exactly one outstanding line. Refuse extra pipelined
  // bytes rather than accumulating an unbounded queue.
  pending = Buffer.concat([pending, chunk]);
  const end = pending.indexOf(10);
  if (end < 0) {
    if (pending.length > REQUEST_LIMIT) return fail(null, 'REQUEST_LIMIT');
    continue;
  }
  if (end > REQUEST_LIMIT) return fail(null, 'REQUEST_LIMIT');
  if (end !== pending.length-1) return fail(null, 'REQUEST_SCHEMA');
  const line = pending.subarray(0,end); pending = Buffer.alloc(0);
  await request(line);
 }
 if (pending.length) await fail(null, 'REQUEST_SCHEMA');
}
main().catch(() => process.exit(1));
