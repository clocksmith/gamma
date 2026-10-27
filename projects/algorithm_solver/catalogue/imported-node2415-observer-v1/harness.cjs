'use strict';
// Native2415 transport successor: observe values, never compute their answer.
// Original prototype chains, own descriptors, links and root must survive.
const fs = require('fs');
// Capture inspection/call primitives before requiring any candidate module.
const ownKeys = Reflect.ownKeys, getDescriptors = Object.getOwnPropertyDescriptors;
const getPrototype = Object.getPrototypeOf, same = Object.is, apply = Reflect.apply;
const isArray = Array.isArray, isInteger = Number.isSafeInteger;
const stringify = JSON.stringify;
const fields = ['val', 'left', 'right'];

function descriptors(node) {
  const keys = ownKeys(node), result = getDescriptors(node);
  if (keys.length !== 3 || !keys.includes('val') || !keys.includes('left') || !keys.includes('right')) {
    throw Error('original own fields changed');
  }
  for (const key of fields) {
    if (!ownKeys(result[key]).includes('value')) throw Error('accessor node field');
  }
  return result;
}

function sameDescriptor(left, right, compareValue) {
  const a = ownKeys(left), b = ownKeys(right);
  if (a.length !== b.length) return false;
  for (const key of a) {
    if (!b.includes(key) || ((compareValue || key !== 'value') && !same(left[key], right[key]))) return false;
  }
  return true;
}

function decodeArgs(args) {
  if (!isArray(args) || args.length !== 1 || args[0] === null || typeof args[0] !== 'object' ||
      ownKeys(args[0]).length !== 1 || !isArray(args[0].__tree_node__)) throw Error('one encoded tree required');
  const values = args[0].__tree_node__, n = values.length;
  if (n < 1 || n > 16383 || ((n + 1) & n)) throw Error('bounded perfect tree required');
  const nodes = [];
  for (const value of values) {
    if (!isInteger(value) || value < 0 || value > 100000) throw Error('bounded integer value required');
    nodes.push({val: value, left: null, right: null});
  }
  for (let i = 0; 2*i+1 < n; i++) { nodes[i].left = nodes[2*i+1]; nodes[i].right = nodes[2*i+2]; }
  return [nodes[0]];
}

function captureNodes(args) {
  const nodes = [args[0]], seen = new Set(), saved = [], before = [], prototypes = new Map();
  for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i];
    if (nodes.length > 200000 || nodes.length > 16383 || node === null || typeof node !== 'object' || seen.has(node)) {
      throw Error('invalid original tree identity');
    }
    seen.add(node);
    const data = descriptors(node), prototype = getPrototype(node);
    if (!isInteger(data.val.value) || data.val.value < 0 || data.val.value > 100000) throw Error('invalid node value');
    for (let p = prototype; p !== null && !prototypes.has(p); p = getPrototype(p)) {
      prototypes.set(p, {parent: getPrototype(p), descriptors: getDescriptors(p)});
    }
    saved.push({data, prototype});
    const state = {value: data.val.value, left: null, right: null};
    for (const key of ['left', 'right']) {
      if (data[key].value !== null) { state[key] = nodes.length; nodes.push(data[key].value); }
    }
    before.push(state);
  }
  const n = nodes.length;
  // Domain-bound traversal: n real nodes, at most 2*n+1 BFS slots = 32767.
  // No change to the historical observer or any executor/identity budget.
  if ((n + 1) & n) throw Error('perfect tree required');
  for (let i = 0; i < n; i++) {
    if (before[i].left !== (2*i+1 < n ? 2*i+1 : null) || before[i].right !== (2*i+2 < n ? 2*i+2 : null)) {
      throw Error('perfect tree required');
    }
  }
  return function finish(result) {
    if (result !== nodes[0] || args[0] !== nodes[0]) throw Error('original root identity changed');
    for (const [prototype, snapshot] of prototypes) {
      if (getPrototype(prototype) !== snapshot.parent) throw Error('original prototype chain changed');
      const current = getDescriptors(prototype), keys = ownKeys(snapshot.descriptors);
      if (ownKeys(current).length !== keys.length) throw Error('original prototype descriptors changed');
      for (const key of keys) {
        if (!ownKeys(current).includes(key) || !sameDescriptor(snapshot.descriptors[key], current[key], true)) {
          throw Error('original prototype descriptors changed');
        }
      }
    }
    const after = [], initialValues = [], finalValues = [];
    for (let i = 0; i < n; i++) {
      if (getPrototype(nodes[i]) !== saved[i].prototype) throw Error('original node prototype changed');
      const current = descriptors(nodes[i]);
      for (const key of fields) {
        // Only val's data value may change; flags and all link values stay exact.
        if (!sameDescriptor(saved[i].data[key], current[key], key !== 'val')) throw Error('original field descriptor changed');
      }
      const value = current.val.value;
      if (!isInteger(value) || value < 0 || value > 100000) throw Error('invalid node value');
      after.push({value, left: before[i].left, right: before[i].right});
      initialValues.push(before[i].value); finalValues.push(value);
    }
    // All physical checks precede successful observation. A verified original
    // tree has no internal aliases, and its identical root is the sole alias.
    return {result: {__tree_node__: finalValues}, result_type: typeof result,
      args_before: [{__tree_node__: initialValues}], args_after: [{__tree_node__: finalValues}],
      alias_edges: [['result', 'args.0']],
      node_identity: {before, after, argument_roots: [0], result_root: 0},
      node_integrity: {schema: 'gamma.native2415-node-integrity.v1', node_count: n,
        class_or_prototype_unchanged: true, own_field_descriptors_unchanged: true}};
  };
}

function main() {
  const packet = JSON.parse(fs.readFileSync('inputs.json'));
  if (packet.entry !== 'solve' || packet.method !== 'solve' || packet.node_identity !== true ||
      !isArray(packet.calls) || packet.calls.length !== 1 || ownKeys(packet.calls[0]).length !== 1 ||
      !ownKeys(packet.calls[0]).includes('args')) throw Error('native2415 requires singleton solve packet');
  let record;
  try {
    const args = decodeArgs(packet.calls[0].args), finish = captureNodes(args);
    const target = require('./program.js');
    if (typeof target !== 'function') throw Error('direct callable CommonJS export required');
    record = {i: 0, ...finish(apply(target, undefined, args))};
  } catch (error) { record = {i: 0, error: String(error).slice(0, 300)}; }
  process.stdout.write(stringify(record) + '\n');
  process.stdout.write(stringify({done: 1}) + '\n');
}
if (require.main === module) main();
module.exports = {decodeArgs, captureNodes};
