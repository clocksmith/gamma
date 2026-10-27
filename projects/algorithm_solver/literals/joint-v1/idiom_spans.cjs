/* Parse only: exact source spans, never evaluation, rewriting or parameter slots. */
'use strict';
const fs = require('node:fs');
const acorn = require('internal/deps/acorn/acorn/dist/acorn');
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const sources = payload.sources, maximum = payload.max_span_bytes;
const maxSpans = payload.max_spans_per_source ?? 2048;
if (!sources || typeof sources !== 'object' || Array.isArray(sources) || !Number.isInteger(maximum) || maximum < 2 || maximum > 512) throw Error('bounded span input required');
if (!Number.isInteger(maxSpans) || maxSpans < 1 || maxSpans > 2048) throw Error('bounded span count required');
const allowed = new Set(['MemberExpression', 'CallExpression', 'BinaryExpression',
  'LogicalExpression', 'UpdateExpression', 'UnaryExpression', 'VariableDeclarator',
  'ReturnStatement', 'VariableDeclaration', 'ExpressionStatement', 'IfStatement', 'ForStatement',
  'ForOfStatement', 'ForInStatement', 'WhileStatement', 'DoWhileStatement', 'TryStatement', 'ThrowStatement', 'NewExpression']);
const result = {}, boundaries = {};
const excluded = new Set();
for (const [key, source] of Object.entries(sources)) {
  if (typeof source !== 'string') throw Error('source text required');
  const tokens = [], comments = [];
  const ast = acorn.parse(source, {ecmaVersion: 2022, sourceType: 'script',
    onToken: tokens, onComment: comments});
  // Python's segmenter indexes Unicode code points, not JavaScript UTF-16 units.
  const offsets = new Map([[0, 0]]);
  let units = 0, points = 0;
  for (const char of source) { units += char.length; offsets.set(units, ++points); }
  const safe = new Set(offsets.keys());
  for (const token of [...tokens, ...comments]) {
    for (let i = token.start + 1; i < token.end; i++) safe.delete(i);
  }
  boundaries[key] = [...safe].map(i => offsets.get(i)).sort((a, b) => a - b);
  const spans = new Set();
  function add(start, end) {
    const text = source.slice(start, end);
    if (safe.has(start) && safe.has(end) && Buffer.byteLength(text) <= maximum && text.trim()) spans.add(text);
    if (spans.size > maxSpans) throw Error('per-source syntactic span budget exceeded');
  }
  function withSpacing(start, end) {
    add(start, end);
    let before = start, after = end;
    while (before > 0 && /\s/.test(source[before - 1])) before--;
    while (after < source.length && /\s/.test(source[after])) after++;
    add(before, end); add(start, after); add(before, after);
  }
  function walk(node) {
    if (!node || typeof node !== 'object') return;
    if (['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(node.type)) {
      excluded.add(source.slice(node.start, node.end));
      if (node.body.type === 'BlockStatement') {
        excluded.add(source.slice(node.body.start, node.body.end));
        if (node.body.body.length) excluded.add(source.slice(node.body.body[0].start, node.body.body.at(-1).end));
      } else excluded.add(source.slice(node.body.start, node.body.end));
    }
    if (allowed.has(node.type)) {
      withSpacing(node.start, node.end);
    }
    if (['ForStatement', 'ForOfStatement', 'ForInStatement', 'WhileStatement',
      'IfStatement', 'FunctionDeclaration'].includes(node.type)) {
      const body = node.body || node.consequent;
      if (body) withSpacing(node.start, body.start + (body.type === 'BlockStatement' ? 1 : 0));
    }
    if (node.type === 'BlockStatement') {
      const body = node.body || [];
      if (body.length) {
        withSpacing(node.start, body[0].start);
        withSpacing(body[body.length - 1].end, node.end);
      }
    }
    // Whole leaf tokens and their adjacent syntax. Never slice a name, string,
    // operator or numeric constant, including in another source's segmentation.
    if (['Identifier', 'Literal', 'ThisExpression'].includes(node.type)) {
      withSpacing(node.start, node.end);
      const index = tokens.findIndex(token => token.start === node.start && token.end === node.end);
      if (index >= 0) {
        const syntax = token => token && token.end > token.start &&
          !/[\w$'"`]/u.test(source.slice(token.start, token.end));
        const before = tokens[index - 1], after = tokens[index + 1];
        if (syntax(before)) withSpacing(before.start, node.end);
        if (syntax(after)) withSpacing(node.start, after.end);
        if (syntax(before) && syntax(after)) withSpacing(before.start, after.end);
      }
    }
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
const output = JSON.stringify({parser: `acorn-${acorn.version}`, spans: result, boundaries, excluded_units: [...excluded].sort()});
if (Buffer.byteLength(output) > 32 * 1024 * 1024) throw Error('syntactic output byte budget exceeded');
process.stdout.write(output);
