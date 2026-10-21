"use strict";
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {fragments}=require('../rewrite-v1/fragment-proposals.cjs');
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
function main(run){
 run=path.resolve(run);const old=path.resolve(__dirname,'../rewrite-v1');
 const c=JSON.parse(fs.readFileSync(path.join(run,'contract.json')));
 const raw=fs.readFileSync(path.join(old,'proposals.json'));if(sha(raw)!==c.prior_source_pool_sha256)throw Error('old pool drift');
 const rows=JSON.parse(raw).rows.map(r=>({...r,file:path.resolve(old,r.file),receipt_kind:'previous80'}));
 const q=JSON.parse(fs.readFileSync(path.join(run,'qualification/report.json'))),by=new Map(q.rows.map(r=>[r.id+'/'+r.variant,r]));
 const m=JSON.parse(fs.readFileSync(path.join(run,'generated/manifest.json')));
 for(const r of m.rows){
  if(r.variant==='original')continue;
  const v=by.get(r.id+'/'+r.variant);if(!v?.passed||v.sha256!==r.sha256)continue;
  const file=path.join(run,'generated',r.file),text=fs.readFileSync(file,'utf8');if(sha(text)!==r.sha256)throw Error('source drift');
  rows.push({...r,file,...fragments(text),receipt_kind:'new20'});
 }
 const p={schema:'gamma.literal-scale100-pool.v1',rows,generator_sha256:sha(fs.readFileSync(__filename)),qualification_sha256:sha(fs.readFileSync(path.join(run,'qualification/report.json')))};
 fs.writeFileSync(path.join(run,'pool.json'),JSON.stringify(p)+'\n');
 console.log(JSON.stringify({problems:new Set(rows.map(r=>r.id)).size,source_choices:rows.length}));
}
if(require.main===module)main(process.argv[2]);
