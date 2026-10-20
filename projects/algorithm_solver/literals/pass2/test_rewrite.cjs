'use strict';
const assert = require('assert/strict');
const {rewrite, HELPER} = require('./rewrite.cjs');
let passed=0;
function test(name, fn) { fn(); passed++; console.log('PASS '+name); }
const fn = body => 'function solve(values) {\n  '+body+'\n}\n';
const frequency='const counts = new Map();\n  for (const value of values) { counts.set(value, (counts.get(value) || 0) + 1); }';
function changed(source, rule) {
 const r=rewrite(source); assert.equal(r.status,'rewritten'); assert.equal(r.rule,rule);
 assert(r.source.startsWith(HELPER+'\n')); assert(r.tail_preserved);
 const {start,end}=r.input_span_utf16;
 assert(r.source.endsWith(source.slice(end))); assert.equal(r.helper_bytes,167);return r;
}
function unchanged(source) {const r=rewrite(source);assert.equal(r.status,'unchanged');assert.equal(r.source,source);assert.equal(r.source_sha256,r.output_sha256);}
test('frequency block exact tail',()=>changed(fn(frequency+'\n  return counts.size; // tail retained'), 'inline-map-frequency-to-shared-helper'));
test('frequency single expression loop',()=>changed(fn(frequency.replace('{ counts.set','counts.set').replace(' + 1); }',' + 1);')+'\n  return counts.size;'),'inline-map-frequency-to-shared-helper'));
test('set cardinality',()=>changed(fn('return Math.min(new Set(values).size, Math.floor(values.length / 2));'),'set-cardinality-to-frequency-cardinality'));
test('set membership query',()=>changed(fn('const counts = new Set(values);\n  return counts.has(1) && counts.size > 0;'),'set-membership-to-frequency-membership'));
test('xor reduce',()=>changed(fn('return values.reduce((result, value) => result ^ value, 0);'),'xor-fold-to-count-parity'));
test('wrong count increment',()=>unchanged(fn(frequency.replace('+ 1','+ 2')+'\n return counts.size;')));
test('wrong count fallback',()=>unchanged(fn(frequency.replace('|| 0','|| 1')+'\n return counts.size;')));
test('wrong loop iterable',()=>unchanged(fn(frequency.replace('of values','of other')+'\n return counts.size;')));
test('wrong loop binding',()=>unchanged(fn(frequency.replace('const value','let value')+'\n return counts.size;')));
test('map constructor data',()=>unchanged(fn(frequency.replace('new Map()','new Map(values)')+'\n return counts.size;')));
test('canonical name mismatch',()=>unchanged(fn(frequency.replaceAll('counts','frequencies')+'\n return frequencies.size;')));
test('helper collision',()=>unchanged(fn(frequency+'\n return countValues(values);')));
test('receiver arguments dynamic context',()=>{for(const tail of ['this.x','arguments[0]','eval("1")','Function("return 1")','globalThis.x'])unchanged(fn(frequency+'\n return '+tail+';'));});
test('intrinsic destructuring shadow',()=>unchanged(fn(frequency+'\n const {Map} = values; return counts.size;')));
test('set mutation refused',()=>{for(const tail of ['counts.add(1); return 0;','counts.delete(1); return 0;','return [...counts];','return counts;','const f=counts.has; return 0;','counts.size=1; return 0;','({x:counts.size}=values); return 0;','for(counts.size of values){} return 0;'])unchanged(fn('const counts=new Set(values); '+tail));});
test('set alias and nested shadow refused',()=>{unchanged(fn('const counts=new Set(values); const copy=counts; return copy.size;'));unchanged(fn('const counts=new Set(values); function f(counts){return counts.size;} return counts.size;'));});
test('set unused refused',()=>unchanged(fn('const counts=new Set(values); return 1;')));
test('set cardinality rounding changed',()=>unchanged(fn('return Math.min(new Set(values).size, Math.ceil(values.length / 2));')));
test('set cardinality extra statement',()=>unchanged(fn('const result=1; return Math.min(new Set(values).size, Math.floor(values.length / 2));')));
test('xor initializer and operator',()=>{unchanged(fn('return values.reduce((result, value) => result ^ value, 1);'));unchanged(fn('return values.reduce((result, value) => result + value, 0);'));});
test('xor callback extra argument',()=>unchanged(fn('return values.reduce((result, value, index) => result ^ value, 0);')));
test('multiple declarations and unsupported source',()=>{unchanged('function helper(){} '+fn('return 1;'));unchanged(fn('return values.length;'));unchanged('bad {');});
test('with rejected',()=>unchanged(fn(frequency+'\n with(values) { return counts.size; }')));
test('CRLF retained not normalized',()=>{const source=fn(frequency+'\n return counts.size;').replaceAll('\n','\r\n');const r=changed(source,'inline-map-frequency-to-shared-helper');assert(r.source.includes('\r\n'));});

test('source reflection refused',()=>unchanged(fn(frequency+'\n return solve.toString();')));
console.log(JSON.stringify({methods:passed,candidate_execution:false,fixture_access:false}));
