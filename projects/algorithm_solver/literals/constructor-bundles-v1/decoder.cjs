// Independent mixed decoder. IDs pay for L/P/I roots and every operand.
const fs = require('node:fs');
const crypto = require('node:crypto');
const acorn = require('/usr/share/nodejs/acorn');
const LIMIT = 4*1024*1024;
const hash = value => crypto.createHash('sha256').update(value).digest();
const ascii = value => typeof value === 'string' && /^[\x00-\x7f]*$/.test(value);
const prefixKinds = new Set(['BinaryExpression','LogicalExpression','AssignmentExpression','UnaryExpression','UpdateExpression','ParenthesizedExpression','ConditionalExpression','MemberExpression','CallExpression']);
const identifierKinds = new Set(['ForStatement','ForOfStatement','ForInStatement','WhileStatement','DoWhileStatement','IfStatement','ReturnStatement','VariableDeclaration','ExpressionStatement','AssignmentExpression','CallExpression','BinaryExpression','LogicalExpression','ConditionalExpression','NewExpression','MemberExpression','ArrayExpression','ObjectExpression','UnaryExpression','UpdateExpression']);
const pathFields = new Set(['left','right','argument','expression','test','consequent','alternate','object','property','callee','arguments']);
function expression(text) {
  const n = acorn.parseExpressionAt(text,0,{ecmaVersion:2022,preserveParens:true});
  if (n.start !== 0 || n.end !== text.length) throw Error('complete expression required');
  return n;
}
function identifier(text) {
  if (!/^[A-Za-z_$][A-Za-z0-9_$]*$/.test(text)) return false;
  try {
    const params = acorn.parse('function __arg('+text+'){}',{ecmaVersion:2022}).body[0].params;
    return params.length === 1 && params[0].type === 'Identifier' && params[0].name === text;
  } catch { return false; }
}
function identifierShape(text,kind,holes) {
  let node, shift = 0;
  if (kind.endsWith('Statement') || kind === 'VariableDeclaration') {
    const prefix = 'function __decoded(){';
    shift = prefix.length;
    const body = acorn.parse(prefix+text+'}',{ecmaVersion:2022}).body[0].body.body;
    if (body.length !== 1) throw Error('one template root required');
    node = body[0];
  } else {
    node = acorn.parseExpressionAt(text,0,{ecmaVersion:2022});
    if (node.start !== 0 || node.end !== text.length) throw Error('one expression root required');
  }
  if (node.type !== kind) throw Error('template root mismatch');
  const found = new Set();
  function walk(n) {
    if (n.type === 'Identifier') found.add(JSON.stringify([n.start-shift,n.end-shift,n.name]));
    for (const value of Object.values(n)) {
      if (Array.isArray(value)) {
        for (const child of value) if (child && typeof child.type === 'string') walk(child);
      } else if (value && typeof value.type === 'string') walk(value);
    }
  }
  walk(node);
  if (!holes.every(h => found.has(JSON.stringify(h)))) throw Error('identifier span mismatch');
}
function validateEntry(entry) {
  if (!Array.isArray(entry) || entry.length !== 2) throw Error('entry shape');
  const [kind,s] = entry;
  if (kind === 'L') {
    if (!ascii(s) || !s || s.length > LIMIT) throw Error('literal');
    return;
  }
  if (!s || typeof s !== 'object' || Array.isArray(s)) throw Error('constructor metadata');
  if (kind === 'P') {
    if (!s.fields || !prefixKinds.has(s.fields.type) ||
        !Array.isArray(s.paths) || s.paths.length < 1 || s.paths.length > 3 ||
        !Array.isArray(s.parts) || s.parts.length !== s.paths.length+1 ||
        s.parts.some(x => !ascii(x)) ||
        s.paths.some(p => !Array.isArray(p) || p.length < 1 || p.length > 3 ||
          p.some(k => typeof k === 'string' ? !pathFields.has(k) : !Number.isInteger(k) || k < 0 || k > 2))) throw Error('prefix metadata');
    const fields = Object.keys(s.fields);
    if (fields.some(k => !['type','operator','prefix','computed','optional'].includes(k))) throw Error('prefix fields');
    const fixed = s.parts.reduce((a,b) => a+b.length,0);
    if (fixed < 1 || fixed > 32) throw Error('prefix fixed text');
  } else if (kind === 'I') {
    if (!identifierKinds.has(s.kind) || !Number.isInteger(s.arity) || s.arity < 1 || s.arity > 4 ||
        !Array.isArray(s.parts) || !Array.isArray(s.uses) || s.parts.length !== s.uses.length+1 ||
        s.uses.length < s.arity || s.uses.length > 16 || s.parts.some(x => !ascii(x)) ||
        s.uses.some(x => !Number.isInteger(x) || x < 0 || x >= s.arity) ||
        new Set(s.uses).size !== s.arity) throw Error('identifier metadata');
    const fixed = s.parts.reduce((a,b) => a+b.length,0);
    if (fixed < 2 || fixed > 96) throw Error('identifier fixed text');
  } else throw Error('entry kind');
}
function decode(db,packet) {
  if (db.subarray(0,4).toString() !== 'STD1') throw Error('dictionary magic');
  const entries = JSON.parse(db.subarray(4).toString('utf8'));
  if (!Array.isArray(entries) || entries.length < 1 || entries.length > 256 ||
      new Set(entries.map(x => JSON.stringify(x))).size !== entries.length) throw Error('dictionary size/duplicates');
  entries.forEach(validateEntry);
  if (packet.length < 41 || packet.subarray(0,4).toString() !== 'STB1' || packet[4] !== 8 ||
      !packet.subarray(5,37).equals(hash(db))) throw Error('packet header');
  const count = packet.readUInt32BE(37);
  if (packet.length !== 41+count) throw Error('packet length');
  const ids = [...packet.subarray(41)];
  if (ids.some(i => i >= entries.length)) throw Error('unused ID');
  let cursor = 0;
  const expansions = [];
  function read(asExpression,depth) {
    if (depth > 8 || cursor >= ids.length) throw Error('depth/truncated operand');
    const [kind,s] = entries[ids[cursor++]];
    if (kind === 'L') {
      if (asExpression) expression(s);
      return {text:s,generated:0};
    }
    if (kind === 'I') {
      if (asExpression) throw Error('identifier template inside prefix forbidden');
      const args = [];
      for (let i=0;i<s.arity;i++) {
        if (cursor >= ids.length) throw Error('truncated identifier argument');
        const arg = entries[ids[cursor++]];
        if (arg[0] !== 'L' || !identifier(arg[1])) throw Error('literal identifier argument required');
        args.push(arg[1]);
      }
      if (new Set(args).size !== args.length) throw Error('distinct identifier arguments required');
      let text = s.parts[0];
      const holes = [];
      for (let i=0;i<s.uses.length;i++) {
        const name = args[s.uses[i]];
        holes.push([text.length,text.length+name.length,name]);
        if (text.length+name.length+s.parts[i+1].length > LIMIT) throw Error('expansion limit');
        text += name+s.parts[i+1];
      }
      identifierShape(text,s.kind,holes);
      const generated = text.length-args.reduce((a,b) => a+b.length,0);
      expansions.push({text,generated});
      return {text,generated};
    }
    if (depth >= 8) throw Error('prefix depth limit');
    let text = s.parts[0], generated = s.parts.reduce((a,b) => a+b.length,0);
    const spans = [];
    for (let i=0;i<s.paths.length;i++) {
      const child = read(true,depth+1);
      spans.push([text.length,text.length+child.text.length]);
      if (text.length+child.text.length+s.parts[i+1].length > LIMIT) throw Error('expansion limit');
      text += child.text+s.parts[i+1];
      generated += child.generated;
    }
    const root = expression(text);
    for (const [field,value] of Object.entries(s.fields)) if (root[field] !== value) throw Error('prefix result kind');
    for (let i=0;i<s.paths.length;i++) {
      let child = root;
      for (const field of s.paths[i]) {
        if (!child || !Object.hasOwn(child,field)) throw Error('prefix child path');
        child = child[field];
      }
      if (child.start !== spans[i][0] || child.end !== spans[i][1]) throw Error('prefix child boundary');
    }
    expansions.push({text,generated});
    return {text,generated};
  }
  let out = '';
  while (cursor < ids.length) {
    const piece = read(false,0).text;
    if (out.length+piece.length > LIMIT) throw Error('output limit');
    out += piece;
  }
  const ast = acorn.parse(out,{ecmaVersion:2022});
  const bodies = new Set([out]);
  let solveFound = false;
  for (const n of ast.body) {
    const functions = [];
    if (n.type === 'FunctionDeclaration' && n.id?.name === 'solve') functions.push(n);
    if (n.type === 'VariableDeclaration') {
      for (const d of n.declarations) {
        if (d.id.name === 'solve' && ['FunctionExpression','ArrowFunctionExpression'].includes(d.init?.type)) functions.push(d.init);
      }
    }
    for (const fn of functions) {
      solveFound = true;
      bodies.add(out.slice(fn.start,fn.end));
      bodies.add(out.slice(fn.body.start,fn.body.end));
      if (fn.body.type === 'BlockStatement') bodies.add(out.slice(fn.body.start+1,fn.body.end-1).trim());
    }
  }
  if (!solveFound) throw Error('solve missing');
  if (entries.some(([kind,s]) => kind === 'L' && bodies.has(s))) throw Error('whole-solution literal');
  if (expansions.some(e => bodies.has(e.text) || e.generated*2 >= out.length)) throw Error('whole-solution expansion');
  return out;
}
if (require.main === module) {
  const input = JSON.parse(fs.readFileSync(0,'utf8'));
  const db = Buffer.from(input.dictionary,'base64');
  process.stdout.write(JSON.stringify(Object.fromEntries(Object.entries(input.packets).map(([id,p]) => [id,decode(db,Buffer.from(p,'base64'))]))));
}
module.exports = {decode};
