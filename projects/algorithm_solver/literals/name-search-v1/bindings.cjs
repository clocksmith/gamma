// Scope-resolved spans for globally consistent, injective bound-name substitutions.
const fs = require('node:fs');
const acorn = require('/usr/share/nodejs/acorn');
const scope = require('/usr/share/nodejs/eslint-scope');

function walk(n, visit) {
  visit(n);
  for (const v of Object.values(n)) {
    if (Array.isArray(v)) { for (const x of v) if (x && typeof x.type === 'string') walk(x, visit); }
    else if (v && typeof v.type === 'string') walk(v, visit);
  }
}

function bindings(text) {
  const ast = acorn.parse(text, {ecmaVersion:2022, ranges:true});
  const excluded = new Set(['solve', 'arguments']), all = new Set();
  let unsafe = false;
  walk(ast, n => {
    if (n.type === 'Identifier') all.add(n.name);
    if (n.type === 'WithStatement' || (n.type === 'CallExpression' && n.callee.type === 'Identifier' && n.callee.name === 'eval')) unsafe = true;
    // Name/source reflection is not invariant under alpha-renaming.
    if (n.type === 'MemberExpression' && ((!n.computed && ['name','toString'].includes(n.property.name)) || (n.computed && ['name','toString'].includes(n.property.value)))) unsafe = true;
    if (n.type === 'Property' && n.shorthand) walk(n.value, x => {if(x.type === 'Identifier') excluded.add(x.name);});
    if (['FunctionDeclaration','FunctionExpression','ClassDeclaration','ClassExpression'].includes(n.type) && n.id) excluded.add(n.id.name);
    if (n.type === 'VariableDeclarator' && n.id.type === 'Identifier' && ['FunctionExpression','ArrowFunctionExpression','ClassExpression'].includes(n.init?.type)) excluded.add(n.id.name);
  });
  const manager = scope.analyze(ast, {ecmaVersion:2022, sourceType:'script', optimistic:true});
  for (const r of manager.globalScope.through) excluded.add(r.identifier.name);
  const spans = new Map();
  for (const s of manager.scopes) for (const v of s.variables) {
    if (!v.identifiers.length) continue;
    const nodes = [...v.identifiers, ...v.references.map(r => r.identifier)];
    const group = spans.get(v.name) || new Map();
    for (const n of nodes) group.set(n.start, [n.start,n.end]);
    spans.set(v.name, group);
  }
  const names = unsafe ? [] : [...spans].filter(([n]) => !excluded.has(n)).map(([name,s]) => ({name,spans:[...s.values()].sort((a,b)=>a[0]-b[0])}));
  names.sort((a,b)=>b.spans.length-a.spans.length || (a.name<b.name?-1:a.name>b.name?1:0));
  return {names, reserved:[...all].filter(n=>!names.some(x=>x.name===n)).sort(), unsafe};
}

if (require.main === module) {
  const input = JSON.parse(fs.readFileSync(0,'utf8'));
  process.stdout.write(JSON.stringify(Object.fromEntries(Object.entries(input).map(([k,v])=>[k,bindings(v)]))));
}
module.exports = {bindings};
