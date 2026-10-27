/* Parse only: exact source spans, never evaluation, rewriting or parameter slots. */
'use strict';
const fs = require('node:fs');
const acorn = require('internal/deps/acorn/acorn/dist/acorn');
const sources = JSON.parse(fs.readFileSync(0, 'utf8'));
const allowed = new Set(['MemberExpression', 'CallExpression', 'BinaryExpression',
  'LogicalExpression', 'UpdateExpression', 'UnaryExpression', 'VariableDeclarator']);
const result = {};
for (const [key, source] of Object.entries(sources)) {
  const ast = acorn.parse(source, {ecmaVersion: 2022, sourceType: 'script'});
  const spans = new Set();
  function walk(node) {
    if (!node || typeof node !== 'object') return;
    if (allowed.has(node.type)) {
      const text = source.slice(node.start, node.end);
      if (Buffer.byteLength(text) <= 48 && text.trim() && !/[\r\n]/.test(text)) spans.add(text);
    }
    for (const value of Object.values(node)) {
      if (Array.isArray(value)) value.forEach(walk);
      else if (value && typeof value === 'object') walk(value);
    }
  }
  walk(ast);
  result[key] = [...spans].sort();
}
process.stdout.write(JSON.stringify({parser: `acorn-${acorn.version}`, spans: result}));
