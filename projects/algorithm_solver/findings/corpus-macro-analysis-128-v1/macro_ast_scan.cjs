const fs = require('fs');
const babel = require('/usr/share/nodejs/@babel/core');
const traverse = require('/usr/share/nodejs/@babel/traverse').default;
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const globals=new Set(['Math','Number','BigInt','Array','Map','Set','ListNode','TreeNode','Infinity','undefined','Uint8Array']);
const ignored=new Set(['start','end','loc','extra','leadingComments','trailingComments','innerComments']);
let out=[];
for(const row of input){
 const source=fs.readFileSync(row.source,'utf8');const ast=babel.parseSync(source,{sourceType:'script',configFile:false,babelrc:false});
 traverse(ast,{enter(path){
  const n=path.node;if(!(/Statement$|Declaration$/.test(n.type)) || /Function|VariableDeclaration|Class/.test(n.type)) return;
  const text=source.slice(n.start,n.end);if(text.length<20||text.length>700)return;
  const names=new Map();let count=0;
  function normalize(v,parent,key){
   if(Array.isArray(v))return v.map(x=>normalize(x,parent,key));
   if(!v||typeof v!=='object')return v;
   count++;
   if(v.type==='Identifier'){
    const fixed=globals.has(v.name)||(parent&&((key==='property'&&!parent.computed)||(key==='key'&&!parent.computed)));
    if(fixed)return {type:v.type,name:v.name};
    if(!names.has(v.name))names.set(v.name,'v'+names.size);
    return {type:v.type,name:names.get(v.name)};
   }
   return Object.fromEntries(Object.keys(v).filter(k=>!ignored.has(k)).sort().map(k=>[k,normalize(v[k],v,k)]));
  }
  const shape=normalize(n,null,null);if(count<5)return;
  out.push({id:row.id,language:'javascript',kind:n.type,start:n.start,end:n.end,text,shape,nodes:count,identifiers:[...names.keys()]});
 }});
}
process.stdout.write(JSON.stringify(out));
