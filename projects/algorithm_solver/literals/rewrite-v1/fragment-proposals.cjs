"use strict";
const fs=require('fs'),path=require('path'),crypto=require('crypto'),acorn=require('acorn');
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
function walk(n,f){if(!n||typeof n.type!=='string')return;f(n);for(const v of Object.values(n)){if(Array.isArray(v))v.forEach(x=>walk(x,f));else if(v&&typeof v.type==='string')walk(v,f);}}
function fragments(source){
 const tree=acorn.parse(source,{ecmaVersion:2022}),banned=new Set([source,source.trim()]);let fn;
 walk(tree,n=>{if(n.type==='FunctionDeclaration'&&n.id?.name==='solve')fn=n;if(n.type==='VariableDeclarator'&&n.id?.name==='solve')fn=n.init;});
 if(!fn)throw Error('missing solve');
 banned.add(source.slice(fn.start,fn.end));banned.add(source.slice(fn.body.start,fn.body.end));
 if(fn.body.type==='BlockStatement'){
  banned.add(source.slice(fn.body.start+1,fn.body.end-1).trim());
  if(fn.body.body.length===1){const only=fn.body.body[0];banned.add(source.slice(only.start,only.end));if(only.type==='ReturnStatement'&&only.argument)banned.add(source.slice(only.argument.start,only.argument.end));}
 }
 const out=new Set();const add=s=>{if(s.length>1&&Buffer.byteLength(s)<=512&&!banned.has(s))out.add(s);};
 walk(tree,n=>{
  if(!['Program','Identifier','Literal'].includes(n.type))add(source.slice(n.start,n.end));
  if(n.type==='BlockStatement')for(let start=0;start<n.body.length;start++)for(let end=start+2;end<=Math.min(n.body.length,start+3);end++)add(source.slice(n.body[start].start,n.body[end-1].end));
 });
 return {fragments:[...out].sort(),excluded:[...banned].sort()};
}
function main(root,out){
 const datasets=[['../scale-v2','canonical','compact'],['.']],rows=[],seen=new Set();
 for(const [dir,...variants]of datasets){const base=path.join(root,dir),m=JSON.parse(fs.readFileSync(path.join(base,'generated/manifest.json'))),q=JSON.parse(fs.readFileSync(path.join(base,'qualification/report.json')));
  for(const r of m.rows){if(variants.length&&!variants.includes(r.variant)||r.variant==='original')continue;
   const verdict=q.rows.find(x=>x.id===r.id&&x.variant===r.variant);if(!verdict?.passed||verdict.sha256!==r.sha256)continue;
   const key=r.id+':'+r.sha256;if(seen.has(key))continue;seen.add(key);
   const text=fs.readFileSync(path.join(base,'generated',r.file),'utf8');if(sha(text)!==r.sha256)throw Error('source drift');
   rows.push({id:r.id,variant:dir==='.'?r.variant:'old-'+r.variant,file:path.join(dir,'generated',r.file),sha256:r.sha256,...fragments(text)});
  }
 }
 const result={schema:'gamma.literal-ast-proposals.v1',generator_sha256:sha(fs.readFileSync(__filename)),rows};
 fs.writeFileSync(out,JSON.stringify(result)+'\n');console.log(JSON.stringify({sources:rows.length,raw_fragments:rows.reduce((n,r)=>n+r.fragments.length,0)}));
}
if(require.main===module)main(...process.argv.slice(2));module.exports={fragments};
