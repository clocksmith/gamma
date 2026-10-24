// Copied pure lexical/structural logic; predecessor helpers stay unchanged.
'use strict';
const acorn = require('/usr/share/nodejs/acorn');
const LEXICAL_STDOUT_LIMIT = 32 * 1024 * 1024;
class ParserFailure extends Error {
  constructor(code) { super(code); this.code = code; }
}
function lexicalByteGuard(serialized, limit = LEXICAL_STDOUT_LIMIT) {
  if (Buffer.byteLength(serialized, 'utf8') > limit)
    throw new ParserFailure('LEXICAL_STDOUT_LIMIT');
}
function lexical(input) {
  const output = {};
  for (const [id, text] of Object.entries(input)) {
    if ([...text].some(c => c.codePointAt(0) > 127))
      throw new ParserFailure('ASCII_CONTRACT');
    const tokens = [], comments = [];
    try { acorn.parse(text, {ecmaVersion: 'latest', onToken: tokens, onComment: comments}); }
    catch (_) { throw new ParserFailure('LEXICAL_PARSE'); }
    const labels = Array(text.length).fill('syntax.layout');
    for (const t of tokens) {
      const k = t.type.label;
      let category;
      if (k === 'eof') continue;
      if (k === 'name' || k === 'privateId') category = 'identifier';
      else if (['num','string','regexp','true','false','null','template','invalidTemplate'].includes(k)) category = 'literal';
      else if (t.type.keyword) category = 'syntax.keyword';
      else if (t.type.binop != null || t.type.isAssign || t.type.prefix || t.type.postfix || ['=>','...','?'].includes(k)) category = 'syntax.operator';
      else category = 'syntax.delimiter';
      labels.fill(category, t.start, t.end);
    }
    for (const c of comments) labels.fill('syntax.comment', c.start, c.end);
    output[id] = labels;
  }
  const serialized = JSON.stringify(output);
  lexicalByteGuard(serialized);
  // The old structure helper parses the child's serialized labels before its
  // second parse. Preserve that round trip; no labels are cached or exported.
  return JSON.parse(serialized);
}
function bodies(input) {
  const labels = lexical(input);
  const out = {};
  for (const [id, text] of Object.entries(input)) {
    let ast;
    try { ast = acorn.parse(text, {ecmaVersion: 'latest'}); }
    catch (_) { throw new ParserFailure('STRUCTURAL_PARSE'); }
    const found = [];
    for (const node of ast.body) {
      const functions = [];
      if (node.type === 'FunctionDeclaration' && node.id?.name === 'solve') functions.push(node);
      if (node.type === 'VariableDeclaration') for (const d of node.declarations)
        if (d.id.name === 'solve' && ['FunctionExpression','ArrowFunctionExpression'].includes(d.init?.type)) functions.push(d.init);
      for (const fn of functions) {
        found.push(text.slice(fn.start, fn.end));
        found.push(text.slice(fn.body.start, fn.body.end));
        if (fn.body.type === 'BlockStatement') found.push(text.slice(fn.body.start+1, fn.body.end-1).trim());
      }
    }
    if (!found.length || found.some(x => !x)) throw new ParserFailure('UNSUPPORTED_SOLVE_BODY');
    out[id] = {labels: labels[id], bodies: found};
  }
  // Retain original Object/JSON behavior before reducing the response to the
  // bodies the existing Python caller actually consumes.
  return Object.fromEntries(Object.entries(out).map(([id, row]) => [id, row.bodies]));
}
module.exports = {bodies, lexical, lexicalByteGuard, LEXICAL_STDOUT_LIMIT, ParserFailure};
