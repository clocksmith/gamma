const fs=require('node:fs'),acorn=require('/usr/share/nodejs/acorn');
const {bindings}=require('../binding-descent-v1/bindings.cjs');
const out={};
for(const [id,text] of Object.entries(JSON.parse(fs.readFileSync(0,'utf8')))){
 const r=bindings(text),ast=acorn.parse(text,{ecmaVersion:2022});r.body_ranges=[];
 for(const n of ast.body){
  const f=[];
  if(n.type==='FunctionDeclaration'&&n.id?.name==='solve')f.push(n);
  if(n.type==='VariableDeclaration')for(const d of n.declarations)if(d.id.name==='solve'&&['FunctionExpression','ArrowFunctionExpression'].includes(d.init?.type))f.push(d.init);
  for(const fn of f){r.body_ranges.push([fn.start,fn.end],[fn.body.start,fn.body.end]);
   if(fn.body.type==='BlockStatement')r.body_ranges.push([fn.body.start+1,fn.body.end-1]);}
 }
 if(!r.body_ranges.length)throw Error('Unsupported solve entry');out[id]=r;
}
process.stdout.write(JSON.stringify(out));
