// Admitted component matches for structural-v1 (DRAFT.md, components.json).
//   node matcher.mjs components.json sources.json > matches.json
// sources.json: {"<id>": "<source text>"}. Output: {"<id>": {"matches": [...], "rejected": {"<cid>": {"<reason>": n}}}}.
// A match is admitted only when every hole covers an AST node of its type, the fixed text matches the
// source bytes exactly, the whole match is the component's declared node kind, and its guards pass.
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const acorn = require('/usr/share/nodejs/acorn');

const EXPRESSIONS = new Set(['Identifier', 'Literal', 'ThisExpression', 'ArrayExpression', 'ObjectExpression', 'FunctionExpression',
  'ArrowFunctionExpression', 'UnaryExpression', 'UpdateExpression', 'BinaryExpression', 'AssignmentExpression', 'LogicalExpression',
  'MemberExpression', 'ConditionalExpression', 'CallExpression', 'NewExpression', 'SequenceExpression', 'TemplateLiteral',
  'TaggedTemplateExpression', 'ClassExpression', 'AwaitExpression', 'YieldExpression', 'ChainExpression', 'ParenthesizedExpression',
  'MetaProperty', 'ImportExpression']);
const IMPURE = new Set(['CallExpression', 'NewExpression', 'AssignmentExpression', 'UpdateExpression', 'AwaitExpression',
  'YieldExpression', 'TaggedTemplateExpression', 'ImportExpression']);
// The node kind each whole match must be (a node type, or 'stmts' for a run of statements in one block).
const KIND = {C1: 'ExpressionStatement', C2: 'ExpressionStatement', C3: 'ExpressionStatement', C4: 'ExpressionStatement',
  C5: 'LogicalExpression', C6: 'ExpressionStatement', C7: 'ExpressionStatement', C8: 'VariableDeclaration', C9: 'stmts',
  Q1: 'WhileStatement', Q2: 'WhileStatement', Q3: 'WhileStatement', Q4: 'stmts', Q5: 'WhileStatement', Q6: 'MemberExpression',
  Q7: 'ExpressionStatement', G1: 'CallExpression', G2: 'ForOfStatement', G3: 'IfStatement', G4: 'IfStatement', G5: 'ForOfStatement',
  G6: 'ForOfStatement', G7: 'ForOfStatement', G8: 'ForOfStatement', G9: 'CallExpression', T1: 'IfStatement', T2: 'CallExpression',
  T3: 'CallExpression', T4: 'stmts', T5: 'stmts', T6: 'stmts', T7: 'WhileStatement'};
const MAP_BOUND = new Set(['C1', 'C2', 'C3', 'C4', 'C5']);
const SET_BOUND = new Set(['G4']);

export function template(text) {
  const parts = []; const re = /\$\{([A-Z])\}/g; let last = 0, m;
  while ((m = re.exec(text))) { if (m.index > last) parts.push({ fixed: text.slice(last, m.index) }); parts.push({ hole: m[1] }); last = re.lastIndex; }
  if (last < text.length) parts.push({ fixed: text.slice(last) });
  return parts;
}

function children(node) {
  const out = [];
  for (const key of Object.keys(node)) {
    if (key === 'type' || key === 'start' || key === 'end') continue;
    const v = node[key];
    if (Array.isArray(v)) { for (const x of v) if (x && typeof x.type === 'string') out.push(x); }
    else if (v && typeof v.type === 'string') out.push(v);
  }
  return out;
}

export function index(text) {
  // UTF-16 offsets from acorn equal JS string indices; the Python side matches on the same JS-index basis (see typed.py).
  const ast = acorn.parse(text, { ecmaVersion: 'latest', sourceType: 'script', preserveParens: true, allowHashBang: true });
  const ident = new Map(), expr = new Map(), runs = new Map(), empty = new Set(), byspan = new Map(), maps = new Set(), sets = new Set();
  const add = (m, k, v) => { if (!m.has(k)) m.set(k, []); m.get(k).push(v); };
  const lists = [];
  (function walk(n) {
    byspan.set(`${n.start}:${n.end}:${n.type}`, n);
    if (n.type === 'Identifier') ident.set(n.start, n.end);
    if (EXPRESSIONS.has(n.type)) add(expr, n.start, n);
    if (n.type === 'Program') lists.push([n.body, n.end]);
    if (n.type === 'BlockStatement' || n.type === 'StaticBlock') lists.push([n.body, n.end - 1]);
    if (n.type === 'VariableDeclarator' && n.id.type === 'Identifier' && n.init && n.init.type === 'NewExpression' && n.init.callee.type === 'Identifier') {
      if (n.init.callee.name === 'Map') maps.add(n.id.name);
      if (n.init.callee.name === 'Set') sets.add(n.id.name);
    }
    for (const c of children(n)) walk(c);
  })(ast);
  for (const [body, end] of lists) {
    for (let i = 0; i < body.length; i++) {
      empty.add(body[i].start);
      for (let j = i; j < body.length; j++) add(runs, body[i].start, { end: body[j].end, statements: body.slice(i, j + 1) });
    }
    empty.add(end);
  }
  return { ast, ident, expr, runs, empty, byspan, maps, sets };
}

function pure(node) {
  if (IMPURE.has(node.type)) return false;
  if (node.type === 'UnaryExpression' && node.operator === 'delete') return false;
  if (node.type === 'FunctionExpression' || node.type === 'ArrowFunctionExpression') return true;  // not evaluated by mention
  return children(node).every(pure);
}

function assigns(nodes, name) {
  let found = false;
  (function walk(n) {
    if ((n.type === 'AssignmentExpression' && n.left.type === 'Identifier' && n.left.name === name) ||
        (n.type === 'UpdateExpression' && n.argument.type === 'Identifier' && n.argument.name === name)) found = true;
    for (const c of children(n)) walk(c);
  })({ type: 'X', body: nodes });
  return found;
}

// Candidate operand spans [s, e) of a hole type starting at s, with the nodes they cover.
function spans(ix, type, s) {
  if (type === 'id') return ix.ident.has(s) ? [{ end: ix.ident.get(s), nodes: null }] : [];
  if (type === 'expr' || type === 'pure') {
    const seen = new Set(), out = [];
    for (const n of ix.expr.get(s) || []) if (!seen.has(n.end) && (type === 'expr' || pure(n))) { seen.add(n.end); out.push({ end: n.end, nodes: [n] }); }
    return out;
  }
  const out = (ix.runs.get(s) || []).map(r => ({ end: r.end, nodes: r.statements }));
  if (ix.empty.has(s)) out.push({ end: s, nodes: [] });
  return out;
}

export function match(text, ix, comp) {
  const parts = template(comp.template), found = [], rejected = {};
  const reject = r => { rejected[r] = (rejected[r] || 0) + 1; };
  const starts = [];
  if (parts[0].fixed) { for (let p = text.indexOf(parts[0].fixed); p >= 0; p = text.indexOf(parts[0].fixed, p + 1)) starts.push(p); }
  else for (let p = 0; p < text.length; p++) starts.push(p);
  for (const start of starts) {
    const results = [];
    (function step(k, p, bound) {
      if (k === parts.length) { results.push({ end: p, bound: { ...bound } }); return; }
      const part = parts[k];
      if (part.fixed !== undefined) { if (text.startsWith(part.fixed, p)) step(k + 1, p + part.fixed.length, bound); return; }
      const h = part.hole, type = comp.holes[h];
      if (bound[h]) { const [s, e] = bound[h].span; const t = text.slice(s, e); if (text.startsWith(t, p)) step(k + 1, p + t.length, bound); return; }
      for (const sp of spans(ix, type, p)) {
        const next = parts[k + 1];
        if (next && next.fixed !== undefined && !text.startsWith(next.fixed, sp.end)) continue;
        bound[h] = { span: [p, sp.end], nodes: sp.nodes }; step(k + 1, sp.end, bound); delete bound[h];
      }
    })(0, start, {});
    for (const r of results) {
      const kind = KIND[comp.id];
      const whole = kind === 'stmts' ? (ix.runs.get(start) || []).some(x => x.end === r.end) : ix.byspan.has(`${start}:${r.end}:${kind}`);
      if (!whole) { reject('not a complete ' + kind); continue; }
      if (kind === 'IfStatement' && ix.byspan.get(`${start}:${r.end}:IfStatement`).alternate) { reject('has else'); continue; }
      const name = h => text.slice(...r.bound[h].span);
      if (MAP_BOUND.has(comp.id) && !ix.maps.has(name('M'))) { reject('M not declared with new Map'); continue; }
      if (SET_BOUND.has(comp.id) && !ix.sets.has(name('S'))) { reject('S not declared with new Set'); continue; }
      if (comp.id === 'T7' && assigns(r.bound.B.nodes, name('P'))) { reject('B reassigns P'); continue; }
      found.push({ c: comp.id, s: start, e: r.end, holes: Object.fromEntries(Object.entries(r.bound).map(([h, b]) => [h, b.span])) });
    }
  }
  return { found, rejected };
}

if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split('/').pop())) {
  const comps = JSON.parse(readFileSync(process.argv[2], 'utf8')).components;
  const sources = JSON.parse(readFileSync(process.argv[3], 'utf8'));
  const out = {};
  for (const [id, text] of Object.entries(sources)) {
    const ix = index(text), row = { matches: [], rejected: {} };
    for (const c of comps) { const { found, rejected } = match(text, ix, c); row.matches.push(...found); if (Object.keys(rejected).length) row.rejected[c.id] = rejected; }
    out[id] = row;
  }
  process.stdout.write(JSON.stringify(out));
}
