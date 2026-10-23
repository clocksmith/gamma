// Identifier roles for roles-v1 (FREEZE.md). Encoder side only: the decoder never needs roles.
//   node roles.mjs < sources.json > roles.json
// sources.json: {"<key>": {"text": "<source>", "interface": ["<name>", ...]}}.
// Output: {"<key>": {"names": [{"name", "role", "ordinal", "spans": [[s, e], ...]}], "excluded": {...}, "identifiers": [...]}}.
// A bound name is any name the program declares (variables, functions, parameters, classes, catch parameters), by
// name and not by scope. Every Identifier node with that name is a span, except property keys, member properties,
// labels and meta-properties. Names in the entry interface, names used as shorthand properties, and every name in a
// program with `with` or direct `eval` stay unbound. Roles by precedence: input, output, index, queue, accumulator, other.
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const acorn = require('/usr/share/nodejs/acorn');

export const ROLES = ['input', 'output', 'index', 'queue', 'accumulator', 'other'];
const FUNCTIONS = new Set(['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression']);

function children(node) {
  const out = [];
  for (const key of Object.keys(node)) {
    if (key === 'type' || key === 'start' || key === 'end') continue;
    const v = node[key];
    if (Array.isArray(v)) { for (const x of v) if (x && typeof x.type === 'string') out.push([key, x]); }
    else if (v && typeof v.type === 'string') out.push([key, v]);
  }
  return out;
}

function walk(node, visit, parent = null, key = null) {
  visit(node, parent, key);
  for (const [k, c] of children(node)) walk(c, visit, node, k);
}

function patternNames(p, out) {
  if (!p) return out;
  if (p.type === 'Identifier') out.push(p.name);
  else if (p.type === 'ObjectPattern') for (const q of p.properties) patternNames(q.type === 'RestElement' ? q.argument : q.value, out);
  else if (p.type === 'ArrayPattern') for (const q of p.elements) patternNames(q, out);
  else if (p.type === 'RestElement') patternNames(p.argument, out);
  else if (p.type === 'AssignmentPattern') patternNames(p.left, out);
  return out;
}

// The function whose parameters are the inputs: a top-level function or arrow bound to the entry name, or the
// method of that name in an interface class (entry form `new Solution().method(...)`).
function entryFunction(ast, entry) {
  let found = null;
  const call = /^\(\.\.\.a\)=>new ([A-Za-z_$][\w$]*)\(\)\.([A-Za-z_$][\w$]*)\(\.\.\.a\)$/.exec(entry);
  for (const st of ast.body) {
    if (!call && st.type === 'FunctionDeclaration' && st.id.name === entry) found = st;
    if (!call && st.type === 'VariableDeclaration')
      for (const d of st.declarations)
        if (d.id.type === 'Identifier' && d.id.name === entry && d.init && FUNCTIONS.has(d.init.type)) found = d.init;
    if (call && st.type === 'ClassDeclaration' && st.id.name === call[1])
      for (const m of st.body.body)
        if (m.type === 'MethodDefinition' && !m.computed && m.key.name === call[2]) found = m.value;
  }
  return found;
}

export function classify(text, iface) {
  const ast = acorn.parse(text, { ecmaVersion: 'latest', sourceType: 'script' });
  const declared = new Set(), forIndex = new Set(), assigned = new Set(), shorthand = new Set();
  const calls = new Map(), occ = new Map(), identifiers = new Set();
  let unsafe = false;
  walk(ast, (n, parent, key) => {
    if (n.type === 'Identifier') identifiers.add(n.name);
    if (n.type === 'VariableDeclarator') patternNames(n.id, []).forEach(x => declared.add(x));
    if (FUNCTIONS.has(n.type)) { if (n.id) declared.add(n.id.name); n.params.forEach(p => patternNames(p, []).forEach(x => declared.add(x))); }
    if ((n.type === 'ClassDeclaration' || n.type === 'ClassExpression') && n.id) declared.add(n.id.name);
    if (n.type === 'CatchClause' && n.param) patternNames(n.param, []).forEach(x => declared.add(x));
    if (n.type === 'ForStatement' && n.init && n.init.type === 'VariableDeclaration')
      n.init.declarations.forEach(d => patternNames(d.id, []).forEach(x => forIndex.add(x)));
    if (n.type === 'AssignmentExpression') patternNames(n.left, []).forEach(x => assigned.add(x));
    if (n.type === 'UpdateExpression' && n.argument.type === 'Identifier') assigned.add(n.argument.name);
    if (n.type === 'Property' && n.shorthand && n.value.type === 'Identifier') shorthand.add(n.value.name);
    if (n.type === 'Property' && n.shorthand && n.value.type === 'AssignmentPattern') shorthand.add(n.value.left.name);
    if (n.type === 'WithStatement') unsafe = true;
    if (n.type === 'CallExpression' && n.callee.type === 'Identifier' && n.callee.name === 'eval') unsafe = true;
    if (n.type === 'CallExpression' && n.callee.type === 'MemberExpression' && !n.callee.computed && n.callee.object.type === 'Identifier') {
      const m = n.callee.property.name;
      if (['push', 'pop', 'shift', 'unshift'].includes(m)) {
        const s = calls.get(n.callee.object.name) || new Set(); s.add(m); calls.set(n.callee.object.name, s);
      }
    }
    if (n.type !== 'Identifier') return;
    const isKey = (parent.type === 'MemberExpression' && key === 'property' && !parent.computed)
      || ((parent.type === 'Property' || parent.type === 'MethodDefinition' || parent.type === 'PropertyDefinition')
          && key === 'key' && !parent.computed && !parent.shorthand)
      || ((parent.type === 'LabeledStatement' || parent.type === 'BreakStatement' || parent.type === 'ContinueStatement') && key === 'label')
      || parent.type === 'MetaProperty';
    if (isKey) return;
    const spans = occ.get(n.name) || []; spans.push([n.start, n.end]); occ.set(n.name, spans);
  });
  const excluded = { interface: [], shorthand: [], unsafe: unsafe ? [...declared].sort() : [] };
  const entry = entryFunction(ast, iface.entry);
  const inputs = new Set(), outputs = new Set();
  if (entry) {
    entry.params.forEach(p => patternNames(p, []).forEach(x => inputs.add(x)));
    const own = (n) => {
      if (n.type === 'ReturnStatement' && n.argument && n.argument.type === 'Identifier') outputs.add(n.argument.name);
      for (const [, c] of children(n)) if (!FUNCTIONS.has(c.type)) own(c);
    };
    own(entry.body);
  }
  const names = [];
  for (const name of declared) {
    if (iface.names.includes(name)) { excluded.interface.push(name); continue; }
    if (shorthand.has(name)) { excluded.shorthand.push(name); continue; }
    if (unsafe) continue;
    const c = calls.get(name);
    const role = inputs.has(name) ? 'input' : outputs.has(name) ? 'output' : forIndex.has(name) ? 'index'
      : c && (c.has('push') || c.has('unshift')) && (c.has('pop') || c.has('shift')) ? 'queue'
      : assigned.has(name) ? 'accumulator' : 'other';
    // Shorthand Property nodes share one Identifier range for key and value; keep each span once.
    const spans = [...new Map((occ.get(name) || []).map(s => [s.join(','), s])).values()].sort((a, b) => a[0] - b[0]);
    if (spans.length) names.push({ name, role, spans });
  }
  names.sort((a, b) => a.spans[0][0] - b.spans[0][0]);
  const next = Object.fromEntries(ROLES.map(r => [r, 0]));
  for (const n of names) n.ordinal = next[n.role]++;
  for (const k of ['interface', 'shorthand']) excluded[k].sort();
  return { names, excluded, identifiers: [...identifiers].sort() };
}

if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split('/').pop())) {
  const input = JSON.parse(readFileSync(0, 'utf8'));
  const out = {};
  for (const [k, v] of Object.entries(input)) out[k] = classify(v.text, v.interface);
  process.stdout.write(JSON.stringify(out));
}
