'use strict';
const assert = require('assert'), path = require('path'), h = require('./native_harness.cjs');
const transport = require(path.join(__dirname, '../../public-domain-qualification-easy16-v1/harness.cjs'));
const UID = 'hack2hire:695aed975242f618a4d2fa2f';
class BufferedFile { constructor(c) { this.c = c; this.held = []; } write(d) { this.held.push(...d); const out = []; while (this.held.length >= this.c) out.push(...this.held.splice(0, this.c)); return out; } flush() { const out = this.held; this.held = []; return out; } }
const args = [['BufferedFile', 'write', 'flush'], [[2], [[1, 2, 3]], []]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({BufferedFile}, UID, {args}, transport);
  assert.deepStrictEqual(r.result, [null, [1, 2], [3]]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'array', 'array']);
  assert.deepStrictEqual(r.args_before, r.args_after);
  assert.deepStrictEqual(r.alias_edges, []);
}
assert.throws(() => h.observe({solve: () => []}, UID, {args}, transport));
assert.throws(() => h.shape(UID, [['BufferedFile'], [[]]]));
const authored = require('./javascript/695aed975242f618a4d2fa2f.js');
const traces = [[['BufferedFile', 'write', 'write', 'flush', 'flush'], [[3], [[1, 2]], [[3, 4, 5, 6, 7]], [], []]], [['BufferedFile', 'flush'], [[1], []]]];
const expected = [[null, [], [1, 2, 3, 4, 5, 6], [7], []], [null, []]];
traces.forEach((t, i) => { const r = h.observe(authored, UID, {args: t}, transport); assert.deepStrictEqual(r.result, expected[i]); assert.deepStrictEqual(r.alias_edges, []); });
console.log('3 source-free JS observer controls + 2 authored-class traces passed');
