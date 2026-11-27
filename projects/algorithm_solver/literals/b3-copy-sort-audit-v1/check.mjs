// Evaluate each callee and its source array in the same fresh JS realm.
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { runInNewContext } from 'node:vm';

const rewriter = process.argv[2] ?? fileURLToPath(new URL('../b3-dict64-transfer-v1/rewriter.mjs', import.meta.url));
const cases = {
  numbers: '[8,7,6,5,4,3,2,1]',
  mixed: '["10",2]',
  sparse: '[8,,6,5,4,3,2,1]',
  bigint: '[2n,1n]',
  signedZero: '[0,-0,1,2,3,-1,3,2]',
  wideNumber: '[9007199254740992,9007199254740994,0,1,-2,3,4,5]',
  getter: '(()=>{const a=[8,7,6,5,4,3,2,1]; Object.defineProperty(a,0,{get(){return ++reads===1?"10":"20"}}); return a})()',
  species: '(()=>{class List extends Array {static get [Symbol.species]() {return class Alt extends Array {}}} return List.of(8,7,6,5,4,3,2,1)})()',
};
const forms = { slice: 'a.slice()', spread: '[...a]' };
const jobs = Object.entries(forms).map(([id, form]) => ({
  id, variant: 'fixed', code: 'function solve(a){return ' + form + '.sort((x,y)=>x-y)}',
}));
const run = spawnSync(process.execPath, [rewriter], { encoding: 'utf8', input: JSON.stringify({ mode: 'batch', jobs }) });
if (run.status !== 0) throw new Error(run.stderr);
const rewritten = JSON.parse(run.stdout).results;
const failures = [];
function observe(code, expression) {
  return runInNewContext(code + ';let reads=0; try { const a=solve(' + expression + ');' +
    'JSON.stringify([reads,a.constructor.name,Array.from({length:a.length},(_,i)=>i in a?' +
    '[typeof a[i],Object.is(-0,a[i])?"-0":String(a[i])]:null)])' +
    '} catch(e) {JSON.stringify([reads,e.name])}', {}, { timeout: 1000 });
}
for (const job of jobs) {
  const result = rewritten.find(row => row.id === job.id);
  if (!result?.ok) throw new Error('rewrite failed for ' + job.id);
  for (const [name, input] of Object.entries(cases)) {
    const expected = observe(job.code, input);
    const actual = observe(result.code, input);
    if (actual !== expected) failures.push({ form: job.id, input: name, expected: JSON.parse(expected), actual: JSON.parse(actual) });
  }
}
console.log(JSON.stringify({ sha256: createHash('sha256').update(readFileSync(rewriter)).digest('hex'),
  cases: jobs.length * Object.keys(cases).length, failures }, null, 2));
process.exitCode = failures.length ? 1 : 0;
