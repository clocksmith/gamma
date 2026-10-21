"use strict";
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const old=require('../scale-v2/generate.cjs'),rw=require('../rewrite-v1/generate.cjs');
const arrow=require('../pass3/generate.cjs').arrow;
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
function arrowSource(source,mode){
 const result=arrow(source);if(result.status!=='rewritten')throw Error(result.reason);return rw.rename(result.source,mode);
}
function main(root){
 const c=JSON.parse(fs.readFileSync(path.join(root,'contract.json'))),out=path.join(root,'generated');
 fs.mkdirSync(out);fs.mkdirSync(path.join(out,'sources'));const rows=[],attempts=[];
 for(const r of c.rows){
  const input=fs.readFileSync(path.join(root,r.source_file),'utf8');if(sha(input)!==r.source_sha256)throw Error('source drift');
  const n=old.normalize(input),seen=new Set();
  for(const [variant,make]of [
   ['original',()=>input],['canonical',()=>n.source],['compact',()=>old.compact(n.source)],
   ['scope',()=>rw.rename(n.source,'scope')],['role',()=>rw.rename(n.source,'role')],
   ['scope-arrow',()=>arrowSource(n.source,'scope')],['role-arrow',()=>arrowSource(n.source,'role')]]){
    try{
     const text=make(),h=sha(text);if(seen.has(h)){attempts.push({id:r.id,variant,status:'duplicate',sha256:h});continue;}
     seen.add(h);const file='sources/'+r.id+'-'+variant+'.js';fs.writeFileSync(path.join(out,file),text);
     rows.push({id:r.id,variant,file,sha256:h,entry:variant==='original'?n.entry:'solve',interface:'named-function',parent_sha256:r.source_sha256});
     attempts.push({id:r.id,variant,status:'generated',sha256:h});
    }catch(e){attempts.push({id:r.id,variant,status:'rejected',reason:String(e)});}
   }
 }
 if(rows.length>c.limits.max_new_sources)throw Error('source limit');
 const m={schema:'gamma.literal-scale100-sources.v1',rows,attempts,contract_sha256:sha(fs.readFileSync(path.join(root,'contract.json'))),generator_sha256:sha(fs.readFileSync(__filename))};
 fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(m,null,2)+'\n');console.log(JSON.stringify({sources:rows.length,attempts:attempts.length,rejected:attempts.filter(a=>a.status==='rejected').length}));
}
if(require.main===module)main(process.argv[2]);
