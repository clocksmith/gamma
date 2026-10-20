"use strict";
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{fragments}=require('../rewrite-v1/fragment-proposals.cjs');
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const run=path.resolve(process.argv[2]),c=JSON.parse(fs.readFileSync(run+'/contract.json'));
const raw=fs.readFileSync(c.prior_run+'/pool.json');if(sha(raw)!==c.prior_pool_sha256)throw Error('prior pool drift');
const rows=JSON.parse(raw).rows.map(r=>({...r})),receipts=[];
for(const dir of [path.resolve(__dirname,'../heap-v1'),run]){
 const qraw=fs.readFileSync(dir+'/qualification/report.json'),q=JSON.parse(qraw),mraw=fs.readFileSync(dir+'/generated/manifest.json'),m=JSON.parse(mraw);
 if(q.generated_manifest_sha256!==sha(mraw)||m.contract_sha256!==sha(fs.readFileSync(dir+'/contract.json')))throw Error('qualification identity');
 if(q.passed_sources!==q.source_count)throw Error('failed source remains outside admitted pool');
 receipts.push({report:dir+'/qualification/report.json',sha256:sha(qraw)});
 for(const r of q.rows){
  if(r.variant==='original')continue;
  const file=path.resolve(dir,'generated',r.file),source=fs.readFileSync(file,'utf8');
  if(!r.passed||r.failures.length||sha(source)!==r.sha256)throw Error('unqualified source');
  rows.push({...r,file,...fragments(source),receipt_kind:dir===run?'row':'heap'});
 }
}
fs.writeFileSync(run+'/pool.json',JSON.stringify({rows,receipts,contract_sha256:sha(fs.readFileSync(run+'/contract.json')),builder_sha256:sha(fs.readFileSync(__filename))},null,2)+'\n');
console.log(JSON.stringify({source_choices:rows.length,problems:new Set(rows.map(r=>r.id)).size}));
