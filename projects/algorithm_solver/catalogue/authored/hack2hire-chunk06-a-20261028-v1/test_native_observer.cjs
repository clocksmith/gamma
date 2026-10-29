'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const F = 'hack2hire:68fbce5f378ce2f46141f920';
class FileSystemStats {
  constructor(files) { this.sizes = files.map((f) => Number(f.split(',')[1])); this.parents = {}; }
  getTotalSize() { return this.sizes.reduce((a, b) => a + b, 0); }
  getCollectionSize() { return 0; }
  getTopCollections() { return []; }
  setParent(c, p) { this.parents[c] = p; }
  getHierarchySize() { return 0; }
}
const args = [['FileSystemStats', 'setParent', 'getTotalSize'], [[['a,3', 'b,4,x']], ['x', 'y'], []]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({FileSystemStats}, F, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, 7]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'number']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({FileSystemStats}, F, {args: [['FileSystemStats', 'getTopCollections'], [[['a,1,x']], [3]]]}, transport);
assert.deepStrictEqual(s.result, [null, []]);
assert.throws(() => h.observe({solve: () => []}, F, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
