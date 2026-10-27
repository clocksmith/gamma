/* Parse-only dependency observations for exact canonical source admission. */
'use strict';
const fs = require('node:fs');
const acorn = require('/usr/share/nodejs/acorn');
const scope = require('/usr/share/nodejs/eslint-scope');
const allowed = new Set(['Array', 'Object', 'Map', 'Set', 'WeakMap', 'WeakSet',
  'Math', 'Number', 'String', 'Boolean', 'BigInt', 'JSON', 'Infinity', 'NaN',
  'undefined', 'Error', 'TypeError', 'RangeError', 'SyntaxError', 'parseInt',
  'parseFloat', 'isNaN', 'isFinite', 'Int8Array', 'Uint8Array', 'Uint8ClampedArray',
  'Int16Array', 'Uint16Array', 'Int32Array', 'Uint32Array', 'Float32Array',
  'Float64Array', 'BigInt64Array', 'BigUint64Array', 'ArrayBuffer', 'DataView',
  'RegExp', 'Symbol', 'module', 'exports']);
const forbiddenProperties = new Set(['random', 'constructor', 'prototype', '__proto__',
  'setPrototypeOf', '__defineGetter__', '__defineSetter__']);

function review(source) {
  if (typeof source !== 'string' || Buffer.byteLength(source) > 65536) throw Error('bounded source required');
  // BITS compiles source as a factory body. Model that lexical scope so a
  // helper declared in the source is not mistaken for an external global.
  // This wrapper is parser input only; no emitted or executed source changes.
  const ast = acorn.parse('(function(){\n' + source + '\n})',
    {ecmaVersion: 2022, sourceType: 'script', ranges: true});
  const manager = scope.analyze(ast, {ecmaVersion: 2022, sourceType: 'script', optimistic: false});
  const globals = [...new Set(manager.globalScope.through.map(r => r.identifier.name))].sort();
  const reasons = new Set(globals.filter(n => !allowed.has(n)).map(n => 'external_name:' + n));
  let nodes = 0;
  const allNodes = [];
  function walk(node) {
    if (++nodes > 20000) throw Error('bounded AST required');
    allNodes.push(node);
    if (['ImportExpression', 'WithStatement', 'AwaitExpression', 'YieldExpression',
      'DebuggerStatement'].includes(node.type) || node.async || node.generator) reasons.add('unsupported_construct:' + node.type);
    if (node.type === 'MemberExpression') {
      const name = node.computed ? node.property.value : node.property.name;
      if (forbiddenProperties.has(name)) reasons.add('reflection_or_nondeterministic_property:' + name);
    }
    if (['CallExpression', 'NewExpression'].includes(node.type) &&
        node.callee.type === 'MemberExpression' && node.callee.computed &&
        node.callee.property.type !== 'Literal') reasons.add('dynamic_member_call');
    for (const value of Object.values(node)) {
      if (Array.isArray(value)) for (const child of value) {
        if (child && typeof child.type === 'string') walk(child);
      }
      else if (value && typeof value.type === 'string') walk(value);
    }
  }
  walk(ast);
  // Follow simple aliases of host objects. Checking only literal Math.random
  // misses `const m=Math; const f=m[key]; f()`. Unknown computed callable
  // extraction remains an explicit review blocker, not an inferred safe call.
  const borrowed = new Set(globals.filter(n => !['undefined', 'Infinity', 'NaN'].includes(n)));
  const dynamicValues = new Set();
  function hostValue(node) {
    if (!node) return false;
    if (node.type === 'Identifier') return borrowed.has(node.name);
    if (node.type === 'MemberExpression') return hostValue(node.object);
    if (node.type === 'ConditionalExpression') return hostValue(node.consequent) || hostValue(node.alternate);
    if (node.type === 'ArrayExpression') return node.elements.some(hostValue);
    if (node.type === 'ObjectExpression') return node.properties.some(p => hostValue(p.value));
    return false;
  }
  for (let round = 0; round <= allNodes.length; round++) {
    const before = borrowed.size + dynamicValues.size;
    for (const node of allNodes) {
      const left = node.type === 'VariableDeclarator' ? node.id : node.type === 'AssignmentExpression' ? node.left : null;
      const right = node.type === 'VariableDeclarator' ? node.init : node.type === 'AssignmentExpression' ? node.right : null;
      if (left?.type !== 'Identifier' || !right) continue;
      if (hostValue(right)) borrowed.add(left.name);
      if ((right.type === 'MemberExpression' && right.computed && right.property.type !== 'Literal') ||
          (right.type === 'Identifier' && dynamicValues.has(right.name))) dynamicValues.add(left.name);
    }
    if (before === borrowed.size + dynamicValues.size) break;
  }
  for (const node of allNodes) {
    if (node.type === 'MemberExpression' && node.computed && node.property.type !== 'Literal' && hostValue(node.object))
      reasons.add('dynamic_host_property');
    if (node.type === 'Property' && forbiddenProperties.has(node.computed ? node.key.value : node.key.name))
      reasons.add('reflection_or_nondeterministic_property:' + (node.computed ? node.key.value : node.key.name));
    if (['CallExpression', 'NewExpression'].includes(node.type) && node.callee.type === 'Identifier' && dynamicValues.has(node.callee.name))
      reasons.add('dynamic_callable_alias');
  }
  return {schema: 'gamma.javascript-static-host-observations.v1', globals,
    unsupported: [...reasons].sort(), ast_nodes: nodes, source_executed: false,
    determinism_proved: false, browser_admitted: false,
    scope: 'Conservative syntax and free-name screen. Dynamic property construction and full behavioral determinism are not proven.'};
}

if (require.main === module) {
  const raw = fs.readFileSync(0, 'utf8');
  if (Buffer.byteLength(raw) > 32 * 1024 * 1024) throw Error('bounded input required');
  const sources = JSON.parse(raw);
  if (!sources || Array.isArray(sources) || Object.keys(sources).length > 4096) throw Error('bounded source map required');
  process.stdout.write(JSON.stringify(Object.fromEntries(Object.entries(sources).map(([id, source]) => [id, review(source)]))));
}
module.exports = {review};
