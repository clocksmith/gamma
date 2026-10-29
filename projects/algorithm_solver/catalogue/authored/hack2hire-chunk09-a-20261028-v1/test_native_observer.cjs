'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:6862f418eb0810914237ab13';
class APIMatchingSystem {
  constructor() { this.paths = new Map(); }
  registerPath(path, handler) { this.paths.set(path, handler); }
  matchPath(path) { return this.paths.get(path) || ''; }
}
const args = [['APIMatchingSystem', 'registerPath', 'matchPath'], [[], ['/a', 'h'], ['/a']]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({APIMatchingSystem}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, 'h']);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'string']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({APIMatchingSystem}, T, {args: [['APIMatchingSystem', 'matchPath'], [[], ['/b']]]}, transport);
assert.deepStrictEqual(s.result, [null, '']);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
