'use strict';
// Offline source rewriting only. The decoder never renames or prints anything.
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const acorn = require('acorn'), scope = require('eslint-scope'), gen = require('escodegen');
const prior = require('../clusters-v1/generate.cjs');
const sha = s => crypto.createHash('sha256').update(s).digest('hex');
const parse = s => acorn.parse(s, {ecmaVersion: 2022, ranges: true});
function walk(n, f) {
  if (!n || typeof n.type !== 'string') return;
  f(n);
  for (const v of Object.values(n)) {
    if (Array.isArray(v)) v.forEach(x => walk(x, f));
    else if (v && typeof v.type === 'string') walk(v, f);
  }
}
function applyNames(tree, names) {
  walk(tree, n => {
    if (n.type === 'Property' && n.shorthand && names.has(n.value)) {
      n.key = {...n.key}; n.shorthand = false;
    }
    if (n.type === 'Identifier' && names.has(n)) n.name = names.get(n);
  });
}
function bindings(tree) {
  return scope.analyze(tree, {ecmaVersion: 2022, sourceType: 'script', optimistic: true});
}
function normalize(source) {
  let tree = parse(source);
  if (tree.body.some(n => n.type === 'ClassDeclaration' && n.id.name === 'Solution')) {
    const result = prior.normal(source);
    return {...result, entry: 'Solution', interface: 'class'};
  }
  const funcs = tree.body.filter(n => n.type === 'FunctionDeclaration');
  if (funcs.length !== 1) throw Error('Expected exactly one public function');
  const entry = funcs[0].id.name, manager = bindings(tree);
  const variable = manager.globalScope.variables.find(v => v.name === entry);
  if (!variable || manager.globalScope.variables.some(v => v.name === 'solve' && v !== variable)) throw Error('Entrypoint binding collision');
  const names = new Map([...variable.identifiers, ...variable.references.map(r => r.identifier)].map(n => [n, 'solve']));
  applyNames(tree, names);
  return {source: gen.generate(tree) + '\n', entry, method: entry, interface: 'named-function'};
}
function compact(source, compactFormat = true) {
  const tree = parse(source), manager = bindings(tree), names = new Map();
  walk(tree, n => {
    if (n.type === 'WithStatement' || n.type === 'Identifier' && ['eval', 'Function'].includes(n.name)) throw Error('Reflective scope unsupported');
  });
  const used = new Set(['solve', 'arguments', ...manager.globalScope.through.map(r => r.identifier.name)]);
  let counter = 0;
  function nextName() {
    while (true) {
      let v = counter++, out = '';
      do { out = String.fromCharCode(97 + v % 26) + out; v = Math.floor(v / 26) - 1; } while (v >= 0);
      if (!used.has(out) && !['do','if','in','of','as','is'].includes(out)) { used.add(out); return out; }
    }
  }
  for (const sc of manager.scopes) for (const variable of sc.variables) {
    if (!variable.defs.length || ['solve', 'arguments'].includes(variable.name)) continue;
    const nodes = [...variable.identifiers, ...variable.references.map(r => r.identifier)];
    const existing = nodes.find(n => names.has(n));
    const name = existing ? names.get(existing) : nextName();
    nodes.forEach(n => names.set(n, name));
  }
  applyNames(tree, names);
  const result = gen.generate(tree, {format: {compact: compactFormat, quotes: 'single', escapeless: false, semicolons: true}}) + '\n';
  if ([...result].some(c => c !== '\n' && (c.charCodeAt(0) < 32 || c.charCodeAt(0) > 126))) throw Error('Non-ASCII output');
  parse(result);
  return result;
}
function canonical(source) {
  // A class has outer and inner bindings sharing its declaration identifier.
  // The historical normalizer assigned that node twice, breaking constructor
  // references. Our binder unifies shared identifier nodes before renaming.
  let hasClass = false;
  walk(parse(source), n => { if (n.type === 'ClassDeclaration') hasClass = true; });
  return hasClass ? compact(source, false) : prior.canonical(source).source;
}
function main(root, out) {
  const contract = JSON.parse(fs.readFileSync(path.join(root, 'contract.json')));
  fs.mkdirSync(out); fs.mkdirSync(path.join(out, 'sources'));
  const rows = [];
  for (const id of [...contract.prior_ids, ...contract.additional_ids].sort((a,b) => a-b)) {
    const original = fs.readFileSync(path.join(root, 'inputs', String(id).padStart(4,'0') + '.js'), 'utf8');
    const n = normalize(original), normalized = canonical(n.source);
    for (const [variant, text] of [['original', original], ['canonical', normalized], ['compact', compact(normalized)]]) {
      const file = 'sources/' + String(id).padStart(4,'0') + '-' + variant + '.js';
      fs.writeFileSync(path.join(out, file), text);
      rows.push({id, variant, file, sha256: sha(text), original_sha256: sha(original), method: n.method,
        entry: variant === 'original' ? n.entry : 'solve', interface: variant === 'original' ? n.interface : 'named-function'});
    }
  }
  const manifest = {schema: 'gamma.literal-scale-sources.v2', rows, contract_sha256: sha(fs.readFileSync(path.join(root,'contract.json'))),
    generator_sha256: sha(fs.readFileSync(__filename)), prior_generator_sha256: sha(fs.readFileSync(path.join(__dirname,'../clusters-v1/generate.cjs')))};
  fs.writeFileSync(path.join(out,'manifest.json'), JSON.stringify(manifest,null,2)+'\n');
  console.log(JSON.stringify({problems: rows.length/3, source_variants: rows.length}));
}
if (require.main === module) main(...process.argv.slice(2));
module.exports = {compact, normalize, canonical};
