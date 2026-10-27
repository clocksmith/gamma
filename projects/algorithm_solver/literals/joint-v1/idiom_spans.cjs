/* Parse only: exact source spans, never evaluation, rewriting or parameter slots. */
'use strict';
const fs = require('node:fs');
const acorn = require('internal/deps/acorn/acorn/dist/acorn');
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const sources = payload.sources;
const maximum = payload.max_span_bytes;
if (!sources || typeof sources !== 'object' || Array.isArray(sources) ||
    !Number.isInteger(maximum) || maximum < 2 || maximum > 512) throw Error('bounded span input required');
const allowed = new Set(['MemberExpression', 'CallExpression', 'BinaryExpression',
  'LogicalExpression', 'UpdateExpression', 'UnaryExpression', 'VariableDeclarator',
  'VariableDeclaration', 'ReturnStatement', 'IfStatement', 'ForStatement',
  'ForOfStatement', 'ForInStatement', 'WhileStatement', 'DoWhileStatement',
  'TryStatement', 'ThrowStatement', 'ExpressionStatement', 'NewExpression']);
const result = {};
const excluded = new Set();
for (const [key, source] of Object.entries(sources)) {
  if (typeof source !== 'string') throw Error('source text required');
  const ast = acorn.parse(source, {ecmaVersion: 2022, sourceType: 'script'});
  const spans = new Set();
  function add(start, end) {
    const text = source.slice(start, end);
    if (Buffer.byteLength(text) <= maximum && text.trim()) spans.add(text);
    if (spans.size > 512) throw Error('per-source syntactic span budget exceeded');
  }
  function walk(node) {
    if (!node || typeof node !== 'object') return;
    if (['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(node.type)) {
      excluded.add(source.slice(node.start, node.end));
      if (node.body.type === 'BlockStatement') {
        excluded.add(source.slice(node.body.start, node.body.end));
        if (node.body.body.length) {
          excluded.add(source.slice(node.body.body[0].start, node.body.body.at(-1).end));
        }
      } else excluded.add(source.slice(node.body.start, node.body.end));
    }
    if (allowed.has(node.type)) add(node.start, node.end);
    for (const value of Object.values(node)) {
      if (Array.isArray(value)) {
        if (value.length && value.every(x => x && /(?:Statement|Declaration)$/.test(x.type))) {
          for (let i = 0; i < value.length; i++) {
            for (const size of [2, 3]) if (i + size <= value.length) add(value[i].start, value[i + size - 1].end);
          }
        }
        value.forEach(walk);
      }
      else if (value && typeof value === 'object') walk(value);
    }
  }
  walk(ast);
  result[key] = [...spans].sort();
}
const output = JSON.stringify({parser: `acorn-${acorn.version}`, spans: result, excluded_units: [...excluded].sort()});
if (Buffer.byteLength(output) > 32 * 1024 * 1024) throw Error('syntactic output byte budget exceeded');
process.stdout.write(output);
