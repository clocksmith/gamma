// Fixed-source AST extraction only. Parent mechanisms remain unchanged.
const fs = require('node:fs');
const prefix = require('../expression-prefix-v1/extract.cjs');
const identifier = require('../identifier-templates-v1/extract.cjs');
const acorn = require('/usr/share/nodejs/acorn');
function extract(text) {
  if (!/^[\x00-\x7f]*$/.test(text)) throw Error('ASCII source required');
  const ast = acorn.parse(text, {ecmaVersion:2022});
  const bodies = new Set([text]);
  let found = false;
  for (const n of ast.body) {
    const functions = [];
    if (n.type === 'FunctionDeclaration' && n.id?.name === 'solve') functions.push(n);
    if (n.type === 'VariableDeclaration') {
      for (const d of n.declarations) {
        if (d.id.name === 'solve' && ['FunctionExpression','ArrowFunctionExpression'].includes(d.init?.type)) functions.push(d.init);
      }
    }
    for (const fn of functions) {
      found = true;
      bodies.add(text.slice(fn.start, fn.end));
      bodies.add(text.slice(fn.body.start, fn.body.end));
      if (fn.body.type === 'BlockStatement') bodies.add(text.slice(fn.body.start+1, fn.body.end-1).trim());
    }
  }
  if (!found) throw Error('solve entry missing');
  return {prefix:prefix.extract(text), identifier:identifier.extract(text), bodies:[...bodies]};
}
if (require.main === module) {
  const input = JSON.parse(fs.readFileSync(0,'utf8'));
  process.stdout.write(JSON.stringify(Object.fromEntries(Object.entries(input).map(([id,text]) => [id,extract(text)]))));
}
module.exports = {extract};
