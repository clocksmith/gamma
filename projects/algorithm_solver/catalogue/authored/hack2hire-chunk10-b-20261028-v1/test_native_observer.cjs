'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:69efc8ea96981f58ae1f6d74';
class TaskManager {
  constructor() { this.names = []; }
  addTask(timestamp, name, priority) { this.names.push(name); return 'taskId' + this.names.length; }
  updateTask(timestamp, taskId, name, priority) { return false; }
  getTask(timestamp, taskId) { return ''; }
}
const args = [['TaskManager', 'addTask', 'getTask'], [[], [1, 'a', 3], [2, 'taskId9']]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({TaskManager}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, 'taskId1', '']);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'string', 'string']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({TaskManager}, T, {args: [['TaskManager', 'updateTask'], [[], [1, 'taskId1', 'x', 0]]]}, transport);
assert.deepStrictEqual(s.result, [null, false]);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
