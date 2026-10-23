const fs = require('node:fs');
const cp = require('node:child_process');
const path = require('node:path');
const acorn = require('/usr/share/nodejs/acorn');
const input = JSON.parse(fs.readFileSync(0,'utf8'));
const labels = JSON.parse(cp.execFileSync(process.execPath,[path.join(__dirname,'../cost-decomposition-v1/lexical.cjs')],{input:JSON.stringify(input),maxBuffer:32*1024*1024,encoding:'utf8'}));
const out = {};
for (const [id,text] of Object.entries(input)) {
  const ast=acorn.parse(text,{ecmaVersion:'latest'}), bodies=[];
  for (const node of ast.body) {
    const functions=[];
    if(node.type==='FunctionDeclaration' && node.id?.name==='solve') functions.push(node);
    if(node.type==='VariableDeclaration') for(const d of node.declarations) if(d.id.name==='solve' && ['FunctionExpression','ArrowFunctionExpression'].includes(d.init?.type)) functions.push(d.init);
    for(const fn of functions) {
      bodies.push(text.slice(fn.start,fn.end));
      bodies.push(text.slice(fn.body.start,fn.body.end));
      if(fn.body.type==='BlockStatement') bodies.push(text.slice(fn.body.start+1,fn.body.end-1).trim());
    }
  }
  if(!bodies.length || bodies.some(x=>!x)) throw Error('Unsupported solve entry body');
  out[id]={labels:labels[id],bodies};
}
process.stdout.write(JSON.stringify(out));
