"use strict";
const fs=require('fs'),path=require('path'),crypto=require('crypto'),acorn=require('acorn');
const {rename}=require('../rewrite-v1/generate.cjs');
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
function main(root){
 const c=JSON.parse(fs.readFileSync(path.join(root,'contract.json')));
 for(const [p,h]of Object.entries(c.inputs))if(sha(fs.readFileSync(path.resolve(root,p)))!==h)throw Error('input drift');
 const sm=JSON.parse(fs.readFileSync(path.join(root,'../scale-v2/generated/manifest.json')));
 const orig=sm.rows.find(r=>r.id===1046&&r.variant==='original');
 const pool=JSON.parse(fs.readFileSync(path.join(root,'../rewrite-v1/proposals.json')));
 const donor=pool.rows.find(r=>r.id===976&&r.variant==='scale-role-3');
 const source=fs.readFileSync(path.resolve(root,'../rewrite-v1',donor.file),'utf8');
 const tree=acorn.parse(source,{ecmaVersion:2022}),node=tree.body.find(n=>n.type==='FunctionDeclaration'&&n.id.name==='h');
 const helper=source.slice(node.start,node.end);if(sha(helper)!==c.helper_sha256)throw Error('helper drift');
 // Keeping a zero after equal stones changes internal iterations but not the
 // nonnegative-multiset outcome; each iteration still removes exactly one item.
 const candidate="function solve(a){if(!Array.isArray(a)||a.length<0||a.length>20000||!a.every(x=>Number.isSafeInteger(x)&&x>=0&&x<=9007199254740991))throw new TypeError('declared input domain');const b=JSON.parse(JSON.stringify(a));for(let i=Math.floor(b.length/2)-1;i>=0;i-=1){h(b,i,b.length);}while(b.length>1){const c=b[0];b[0]=b[b.length-1];b.pop();h(b,0,b.length);b[0]=c-b[0];h(b,0,b.length);}return b.length===0?0:b[0];}"+helper+"\n";
 const out=path.join(root,'generated');fs.mkdirSync(out);fs.mkdirSync(path.join(out,'sources'));
 const rows=[{...orig,file:path.relative(out,path.resolve(root,'../scale-v2/generated',orig.file))}];
 for(const [variant,text]of [['heap-shared',candidate],['heap-scope',rename(candidate,'scope')],['heap-role',rename(candidate,'role')]]){
  const file='sources/1046-'+variant+'.js';fs.writeFileSync(path.join(out,file),text);
  rows.push({id:1046,variant,file,sha256:sha(text),entry:'solve',method:orig.method,interface:'named-function',parent_sha256:orig.sha256});
 }
 const manifest={schema:'gamma.literal-heap-recomposition.v1',rows,helper_sha256:sha(helper),generator_sha256:sha(fs.readFileSync(__filename)),contract_sha256:sha(fs.readFileSync(path.join(root,'contract.json')))};
 fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log(JSON.stringify({original:1,new_sources:3,shared_helper_bytes:Buffer.byteLength(helper)}));
}
if(require.main===module)main(__dirname);
