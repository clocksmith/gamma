// Trusted parser-only transform. Input carries NO audit booleans; they come from
// the externally pinned, independently reviewed composite admission receipt.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
import {alignExtrema}from '../extrema-binding-alignment-v1/alignment-v3.mjs';
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const [outputArg,admissionPath,admissionSha]=process.argv.slice(2),ids=[123,55,1014,1121,1375,1725,1732,2873];
if(!/^[0-9a-f]{64}$/.test(admissionSha||''))throw Error('externally pinned composite admission required');
const raw=fs.readFileSync(admissionPath);if(hash(raw)!==admissionSha)throw Error('admission bytes changed');const admission=JSON.parse(raw);
const guard='e9fda12b87d325df18b69ddf21e0cf82e8a2c55b3966bc0602e058e7fed5db5e';
if(admission.schema!=='gamma.extrema8.transform-admission.v1'||admission.root_parser_transform_authorized!==true||admission.source_pool_admission!==false||admission.guard_sha256!==guard||hash(fs.readFileSync(new URL('../extrema-binding-alignment-v1/alignment-v3.mjs',import.meta.url)))!==guard||JSON.stringify(admission.audits.map(x=>x.problem_id))!==JSON.stringify(ids)||!/^[0-9a-f]{64}$/.test(admission.independent_review_sha256||''))throw Error('trusted exact composite admission identity');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
if(input.schema!=='gamma.extrema8.transform-input.v1'||input.admission_sha256!==admissionSha||JSON.stringify(input.variants.map(v=>Number(v.problem_id)))!==JSON.stringify(ids))throw Error('exact admitted source packet');
const output=path.resolve(outputArg);if(!output.startsWith('/workspace/shared/')||fs.existsSync(output))throw Error('new private transform output required');
const all=[];
for(const mode of ['format','role']){
 const rows=[];
 for(const v of input.variants){
  if(Object.keys(v).sort().join(',')!=='key,problem_id,source,source_sha256'||v.key!==v.problem_id+':original'||hash(v.source)!==v.source_sha256)throw Error('source packet identity or unauthorized audit field');
  const audit=admission.audits.find(r=>r.problem_id===Number(v.problem_id));if(audit.source_sha256!==v.source_sha256)throw Error('source review mismatch');
  const t=alignExtrema(v.source,{sourceSha256:v.source_sha256,audit,mode});rows.push({source:t.source,metadata:{problem_id:v.problem_id,original_sha256:v.source_sha256,[mode+'_sha256']:hash(t.source),original_bytes:Buffer.byteLength(v.source),[mode+'_bytes']:Buffer.byteLength(t.source),changed_bindings:t.changed_bindings.length,eligible_bindings:t.eligible_bindings,ast_verified:t.ast_verified,occurrence_resolution_verified:t.occurrence_resolution_verified,mode,qualification:false,admission_sha256:admissionSha}});
 }
 all.push({mode,rows});
}
fs.mkdirSync(output,{mode:0o700});
for(const arm of all){
 const dir=path.join(output,arm.mode);fs.mkdirSync(dir,{mode:0o700});for(const r of arm.rows)fs.writeFileSync(path.join(dir,r.metadata.problem_id+'.js'),r.source,{mode:0o600,flag:'wx'});
 const manifest={schema:'gamma.extrema8.transformed.v1',ids:ids.map(String),rows:arm.rows.map(r=>r.metadata),admission_sha256:admissionSha,candidate_executions:0,qualified:0,original_variants_retained:875,fit_owners:300};fs.writeFileSync(path.join(dir,'transformations.json'),JSON.stringify(manifest)+'\n',{mode:0o600,flag:'wx'});
}
console.log(JSON.stringify({sources:8,arms:2,transformed_variants:16,candidate_execution:false,qualified:0}));
