'use strict';
const acorn = require('/usr/share/nodejs/acorn');
const crypto = require('crypto');
const HELPER = 'function countValues(values) {\n  const counts = new Map();\n  for (const value of values) {\n    counts.set(value, (counts.get(value) || 0) + 1);\n  }\n  return counts;\n}\n';
const hash = text => crypto.createHash('sha256').update(text).digest('hex');
const id = (node, name) => node && node.type === 'Identifier' && node.name === name;
const literal = (node, value) => node && node.type === 'Literal' && node.value === value;
const member = (node, object, property) => node && node.type === 'MemberExpression' && !node.computed && !node.optional && id(node.object, object) && id(node.property, property);
const call = (node, object, property, arity) => node && node.type === 'CallExpression' && !node.optional && member(node.callee, object, property) && node.arguments.length === arity;
const binary = (node, operator) => node && node.type === 'BinaryExpression' && node.operator === operator;
function walk(node, visit, parent = null, field = null) {
  if (!node || typeof node.type !== 'string') return;
  visit(node, parent, field);
  for (const [key, value] of Object.entries(node)) {
    if (Array.isArray(value)) for (const child of value) walk(child, visit, node, key);
    else if (value && typeof value.type === 'string') walk(value, visit, node, key);
  }
}
function declaration(node, kind) {
  if (!node || node.type !== 'VariableDeclaration' || node.kind !== 'const' || node.declarations.length !== 1) return false;
  const entry = node.declarations[0];
  return id(entry.id, 'counts') && entry.init && entry.init.type === 'NewExpression' && id(entry.init.callee, kind)
    && entry.init.arguments.length === (kind === 'Map' ? 0 : 1)
    && (kind === 'Map' || id(entry.init.arguments[0], 'values'));
}
function incrementLoop(node) {
  if (!node || node.type !== 'ForOfStatement' || node.await || !id(node.right, 'values')) return false;
  const left = node.left;
  if (left.type !== 'VariableDeclaration' || left.kind !== 'const' || left.declarations.length !== 1 || !id(left.declarations[0].id, 'value') || left.declarations[0].init) return false;
  const body = node.body.type === 'BlockStatement' && node.body.body.length === 1 ? node.body.body[0] : node.body;
  if (body.type !== 'ExpressionStatement') return false;
  const expression = body.expression;
  if (!call(expression, 'counts', 'set', 2) || !id(expression.arguments[0], 'value')) return false;
  const sum = expression.arguments[1];
  if (!binary(sum, '+') || !literal(sum.right, 1)) return false;
  const fallback = sum.left;
  return fallback.type === 'LogicalExpression' && fallback.operator === '||' && literal(fallback.right, 0)
    && call(fallback.left, 'counts', 'get', 1) && id(fallback.left.arguments[0], 'value');
}
function soleSetSizeReturn(body) {
  if (body.length !== 1 || body[0].type !== 'ReturnStatement') return false;
  const expression = body[0].argument;
  if (!call(expression, 'Math', 'min', 2)) return false;
  const size = expression.arguments[0], floor = expression.arguments[1];
  return size && size.type === 'MemberExpression' && !size.computed && !size.optional && id(size.property, 'size')
    && size.object.type === 'NewExpression' && id(size.object.callee, 'Set') && size.object.arguments.length === 1 && id(size.object.arguments[0], 'values')
    && call(floor, 'Math', 'floor', 1) && binary(floor.arguments[0], '/') && member(floor.arguments[0].left, 'values', 'length') && literal(floor.arguments[0].right, 2);
}
function soleXorReturn(body) {
  if (body.length !== 1 || body[0].type !== 'ReturnStatement') return false;
  const expression = body[0].argument;
  if (!call(expression, 'values', 'reduce', 2) || !literal(expression.arguments[1], 0)) return false;
  const callback = expression.arguments[0];
  return callback.type === 'ArrowFunctionExpression' && !callback.async && callback.params.length === 2 && id(callback.params[0], 'result') && id(callback.params[1], 'value')
    && binary(callback.body, '^') && id(callback.body.left, 'result') && id(callback.body.right, 'value');
}
function onlyMembershipUses(statements) {
  let valid = true;
  let queries = 0;
  const parents = new Map();
  for (const statement of statements) walk(statement, (node, parent) => parents.set(node, parent));
  for (const statement of statements) walk(statement, (node, parent, field) => {
    if (node.type === 'AssignmentExpression' || node.type === 'ForOfStatement' || node.type === 'ForInStatement') {
      walk(node.left, child => { if (id(child, 'counts')) valid = false; });
    }
    if (!id(node, 'counts')) return;
    queries++;
    if (!parent || field !== 'object' || parent.type !== 'MemberExpression' || parent.computed || parent.optional) { valid = false; return; }
    const outer = parents.get(parent);
    if (id(parent.property, 'has')) {
      if (!outer || outer.type !== 'CallExpression' || outer.callee !== parent || outer.optional || outer.arguments.length !== 1) valid = false;
    } else if (id(parent.property, 'size')) {
      if (!outer || (outer.type === 'AssignmentExpression' && outer.left === parent) || outer.type === 'UpdateExpression' || (outer.type === 'UnaryExpression' && outer.operator === 'delete')) valid = false;
    } else valid = false;
  });
  return valid && queries > 0;
}
function rewrite(source) {
  if (typeof source !== 'string') throw new TypeError('source must be decoded UTF-8 text');
  const unchanged = reason => ({status: 'unchanged', reason, source, source_sha256: hash(source), output_sha256: hash(source)});
  let tree;
  try { tree = acorn.parse(source, {ecmaVersion: 2022, sourceType: 'script'}); }
  catch (_) { return unchanged('parse-rejected'); }
  if (tree.body.length !== 1) return unchanged('not-one-standalone-function');
  const fn = tree.body[0];
  if (fn.type !== 'FunctionDeclaration' || !id(fn.id, 'solve') || fn.async || fn.generator || fn.params.length < 1 || !id(fn.params[0], 'values')
      || fn.params.some(param => param.type !== 'Identifier' || !['values','other','value','length','count'].includes(param.name))
      || new Set(fn.params.map(param => param.name)).size !== fn.params.length) return unchanged('noncanonical-function-interface');
  let unsafe = false;
  walk(tree, (node, parent, field) => {
    if (id(node, 'solve') && !(parent === fn && field === 'id')) unsafe = true;
    if (['ThisExpression','Super','WithStatement','ImportExpression','MetaProperty'].includes(node.type)) unsafe = true;
    if (node.type === 'Identifier' && ['countValues','eval','Function','arguments','globalThis','global','window','process','require','module','exports','Reflect','Proxy'].includes(node.name)) unsafe = true;
    if (node.type === 'MemberExpression' && ((!node.computed && ['constructor','__proto__'].includes(node.property.name)) || (node.computed && node.property.type === 'Literal' && ['constructor','__proto__'].includes(node.property.value)))) unsafe = true;
    // Only accept intrinsic names in their exact expression roles; this also
    // rejects destructured/local bindings and intrinsic mutation targets.
    if (node.type === 'Identifier' && ['Map','Set'].includes(node.name) && !(parent && parent.type === 'NewExpression' && field === 'callee')) unsafe = true;
    if (id(node, 'Math') && !(parent && parent.type === 'MemberExpression' && field === 'object')) unsafe = true;
    if (node.type === 'AssignmentExpression' || node.type === 'UpdateExpression' || (node.type === 'UnaryExpression' && node.operator === 'delete')) {
      walk(node.left || node.argument, child => { if (child.type === 'Identifier' && ['Map','Set','Math'].includes(child.name)) unsafe = true; });
    }
  });
  if (unsafe) return unchanged('forbidden-context-or-helper-collision');
  const body = fn.body.body;
  let rule, start, end, replacement, domain;
  if (declaration(body[0], 'Map') && incrementLoop(body[1])) {
    rule = 'inline-map-frequency-to-shared-helper'; start = body[0].start; end = body[1].end;
    replacement = 'const counts = countValues(values);';
    domain = 'Ordinary dense arrays or strings, unmodified built-in Map and iterator behavior; integer occurrence counts remain exact. Same frequency algorithm and same statement order.';
  } else if (soleSetSizeReturn(body)) {
    rule = 'set-cardinality-to-frequency-cardinality'; start = body[0].argument.arguments[0].object.start; end = body[0].argument.arguments[0].object.end;
    replacement = 'countValues(values)';
    domain = 'Dense finite-integer arrays, unmodified built-ins; SameValueZero key classes unchanged. Counts add per-key numeric storage but no input mutation.';
  } else if (declaration(body[0], 'Set') && onlyMembershipUses(body.slice(1))) {
    rule = 'set-membership-to-frequency-membership'; start = body[0].declarations[0].init.start; end = body[0].declarations[0].init.end;
    replacement = 'countValues(values)';
    domain = 'Ordinary arrays or strings with unmodified iterators/built-ins. Tail may only query counts.has or counts.size; no Set identity/iteration/mutation dependence.';
  } else if (soleXorReturn(body)) {
    rule = 'xor-fold-to-count-parity'; start = body[0].start; end = body[0].end;
    replacement = 'const counts = countValues(values);\n  let result = 0;\n  for (const [value, count] of counts) {\n    if (count % 2) result ^= value;\n  }\n  return result;';
    domain = 'Dense finite signed32 integer arrays. XOR parity equivalence; O(k) additional Map memory replaces O(1). No source-order dependence or input mutation under this domain.';
  } else return unchanged('no-supported-pattern');
  const prefix = source.slice(0,start), tail = source.slice(end);
  const output = HELPER + '\n' + prefix + replacement + tail;
  // Parse emitted bytes only; never evaluate or call the candidate.
  const emitted = acorn.parse(output, {ecmaVersion:2022, sourceType:'script'});
  if (emitted.body.length !== 2 || !id(emitted.body[0].id,'countValues') || !id(emitted.body[1].id,'solve')) throw new Error('unexpected emitted shape');
  return {status:'rewritten',rule,source:output,source_sha256:hash(source),output_sha256:hash(output),
    helper_sha256:hash(HELPER),helper_bytes:Buffer.byteLength(HELPER),input_span_utf16:{start,end},
    input_replaced_bytes:Buffer.byteLength(source.slice(start,end)),replacement_bytes:Buffer.byteLength(replacement),
    unchanged_prefix_sha256:hash(prefix),unchanged_tail_sha256:hash(tail),unchanged_tail_bytes:Buffer.byteLength(tail),domain,
    tail_preserved:output.endsWith(tail),complete_source_counted:true};
}
module.exports = {rewrite, HELPER};
