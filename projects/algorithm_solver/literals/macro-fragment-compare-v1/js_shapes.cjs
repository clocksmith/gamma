// Source-as-data only; byte offsets include exact whitespace and operands.
const fs=require('node:fs');
const acorn=require('internal/deps/acorn/acorn/dist/acorn');
const sources=JSON.parse(fs.readFileSync(0,'utf8'));const out={};
for(const [id,source] of Object.entries(sources)){
 const tokens=[];const tree=acorn.parse(source,{ecmaVersion:2022,onToken:tokens});
 const byte=n=>Buffer.byteLength(source.slice(0,n));const nodes=[],banned=[];
 function walk(n){
  if(!n||typeof n!=='object')return;
  const children=[];
  for(const [key,v]of Object.entries(n)){
   if(['start','end','type'].includes(key))continue;
   for(const c of Array.isArray(v)?v:[v])if(c&&typeof c==='object'&&c.type){children.push(c);walk(c);}
  }
  if(/Function|Class/.test(n.type)||n.type==='MethodDefinition'||(n.type==='Property'&&n.method)){
   banned.push([byte(n.start),byte(n.end)]);
   if(n.body?.type==='BlockStatement'&&n.body.body.length)banned.push([byte(n.body.body[0].start),byte(n.body.body.at(-1).end)]);
   else if(n.body)banned.push([byte(n.body.start),byte(n.body.end)]);
  }
  if(!['Program','BlockStatement','FunctionDeclaration','FunctionExpression','ArrowFunctionExpression','ClassDeclaration','ClassExpression','MethodDefinition'].includes(n.type))
   nodes.push([byte(n.start),byte(n.end),children.map(c=>[byte(c.start),byte(c.end)]),n.type]);
 }
 walk(tree);out[id]={tokens:tokens.filter(t=>t.end>t.start).map(t=>[byte(t.start),byte(t.end)]),nodes,banned};
}
process.stdout.write(JSON.stringify(out));
