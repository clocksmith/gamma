'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const OOV = 'hack2hire:688aefae3867670cfb894129', PST = 'hack2hire:677f4db36fee41e51af73dd6';
class VisitorTracker {
  constructor() { this.log = []; }
  login(username) { this.log.push(username); }
  getOldestOneTimeVisitor() { return this.log.find((u) => this.log.filter((v) => v === u).length === 1) ?? ''; }
}
class PStack {
  constructor() { this.versions = [[]]; this.base = [null]; }
  push(version, val) { this.versions.push([...this.versions[version], val]); this.base.push(version); return this.versions.length - 1; }
  pop(version) { return this.base[version]; }
  peek(version) { return this.versions[version].at(-1); }
  size(version) { return this.versions[version].length; }
}
const args = [['VisitorTracker', 'login', 'getOldestOneTimeVisitor'], [[], ['ann'], []]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({VisitorTracker}, OOV, {args}, transport);
  assert.deepStrictEqual(r.result, [null, null, 'ann']);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'undefined', 'string']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({PStack}, PST, {args: [['PStack', 'push', 'push', 'peek', 'pop', 'size'], [[], [0, 4], [1, 2], [2], [2], [1]]]}, transport);
assert.deepStrictEqual(s.result, [null, 1, 2, 2, 1, 1]);
assert.deepStrictEqual(s.native_method_return_types, ['constructed', 'number', 'number', 'number', 'number', 'number']);
assert.throws(() => h.observe({solve: () => []}, OOV, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
assert.throws(() => h.shape(PST, [['PStack', 'push'], [[], [0]]]));
console.log('5 source-free JS observer controls passed');
