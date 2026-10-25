import assert from 'node:assert/strict';
import {canonicalize} from './canonicalize.mjs';
const examples=[
 'function solve(longName){let answer=longName+1;return answer;}',
 'function solve(a){let z=1;{let b=a+z;z=b;}return z;}',
 'function solve(a){return a + +a;}',
 'function solve(a){return a - -a;}',
 'function solve(a){return /x/g.test(a);}',
 'function solve(a){return `x${a}`;}',
 'function solve(a){let z={a};return z.a;}',
 'function solve(a){return 1 .toFixed(a);}',
 'function solve(a){let b=0;for(let c of a)b+=c;return b;}',
 'function solve(a){function nested(b){return a+b;}return nested(1);}'
];
let accepted=0,rejected=0;
for(const source of examples){try{const r=canonicalize(source);assert(r.ast_verified);assert.equal(r.candidate_executions,0);accepted++;}catch(e){if(!/unsafe source|printer changed AST/.test(String(e)))throw e;rejected++;}}
assert(accepted>=7);assert.throws(()=>canonicalize('function solve(a){return eval(a);}'),/unsafe/);
console.log(JSON.stringify({accepted,rejected,candidate_executions:0}));
