// Trusted parser-only transformation. Never eval/import submitted source strings.
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import {align} from './alignment.mjs';
import {numericIndexProof} from './numeric-index-proof-v2.mjs';
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const input=JSON.parse(fs.readFileSync(0,'utf8')),ids=['747','922','1791','1823','3100','3192'];
if(input.schema!=='gamma.six-role-alignment.transform-input.v1'||JSON.stringify(input.ids)!==JSON.stringify(ids)||Object.keys(input.sources).sort().join(',')!==[...ids].sort().join(','))throw Error('exact six source identities required');
const output=path.resolve(process.argv[2]);
if(!output.startsWith('/workspace/shared/')||fs.existsSync(output))throw Error('new private output required');
const transformed=[];
for(const id of ids){
 const row=input.sources[id];if(hash(row.source)!==row.sha256||row.audit.source_sha256!==row.sha256)throw Error('source audit identity');
 const proof=numericIndexProof(row.source);if(!proof.all_computed_indices_inductively_numeric)throw Error('definite numeric index proof failed');
 const result=align(row.source,{audit:row.audit,sourceSha256:row.sha256,mode:'format'});
 transformed.push({id,source:result.source,metadata:{problem_id:id,original_sha256:row.sha256,format_sha256:hash(result.source),original_bytes:Buffer.byteLength(row.source),format_bytes:Buffer.byteLength(result.source),changed_bindings:result.changed_bindings.length,eligible_bindings:result.eligible_bindings,ast_verified:result.ast_verified,occurrence_resolution_verified:result.occurrence_resolution_verified,numeric_index_proof_verified:true,qualification:false,mode:'format',original_fallback_retained:true,admission_scope:row.audit.scope}});
}
fs.mkdirSync(output,{mode:0o700});
for(const row of transformed)fs.writeFileSync(path.join(output,row.id+'.js'),row.source,{mode:0o600,flag:'wx'});
const report={schema:'gamma.six-role-alignment.transformed.v1',ids,rows:transformed.map(x=>x.metadata),candidate_executions:0,qualified:0,fit_owners:300,original_variants_retained:875,old_receipts_modified:false};
fs.writeFileSync(path.join(output,'transformations.json'),JSON.stringify(report)+'\n',{mode:0o600,flag:'wx'});
console.log(JSON.stringify({sources:6,candidate_executions:0,transformed_manifest_sha256:hash(JSON.stringify(report)+'\n'),original_bytes:report.rows.reduce((s,r)=>s+r.original_bytes,0),format_bytes:report.rows.reduce((s,r)=>s+r.format_bytes,0)}));
