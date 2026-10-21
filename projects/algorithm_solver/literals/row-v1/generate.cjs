"use strict";
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{rename}=require('../rewrite-v1/generate.cjs');
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
function main(run){
 const c=JSON.parse(fs.readFileSync(path.join(run,'contract.json'))),p=JSON.parse(fs.readFileSync(path.join(run,'proposals.json'))),helper=fs.readFileSync(__dirname+'/row.js','utf8');
 if(sha(helper)!==c.helper_sha256||sha(fs.readFileSync(path.join(run,'proposals.json')))!==c.proposal_sha256)throw Error('input drift');
 const out=path.join(run,'generated');fs.mkdirSync(out);fs.mkdirSync(path.join(out,'sources'));const rows=[],attempts=[];
 for(const r of c.rows){
  const original=fs.readFileSync(path.join(run,r.source_file),'utf8'),body=p[r.id]+helper;
  if(sha(original)!==r.source_sha256)throw Error('source drift');
  for(const [variant,make]of [['original',()=>original],['row-authored',()=>body],['row-scope',()=>rename(body,'scope')],['row-role',()=>rename(body,'role')]]){
   try{const source=make(),file='sources/'+r.id+'-'+variant+'.js';fs.writeFileSync(path.join(out,file),source);rows.push({id:r.id,variant,file,sha256:sha(source),entry:'solve',interface:'named-function',parent_sha256:r.source_sha256});attempts.push({id:r.id,variant,status:'generated'});}
   catch(e){attempts.push({id:r.id,variant,status:'rejected',reason:String(e)});}
  }
 }
 if(rows.length>c.limits.max_sources)throw Error('source limit');
 fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify({rows,attempts,contract_sha256:sha(fs.readFileSync(path.join(run,'contract.json')))},null,2)+'\n');
 console.log(JSON.stringify({sources:rows.length,rejected:attempts.filter(a=>a.status==='rejected').length}));
}
if(require.main===module)main(process.argv[2]);
