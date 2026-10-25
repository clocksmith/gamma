// Read an explicitly gated/pinned fit-only packet; parse sources as inert strings.
// stdout contains private metadata only; never publish this per-variant stream.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {strictSubset,resolution} from './alignment.mjs';
import {numericIndexProof} from './numeric-index-proof-v2.mjs';
import {controls} from './numeric-index-controls-v2.mjs';
const proofControls=controls();
console.log(JSON.stringify({numeric_index_controls:proofControls}));
if(proofControls.some(x=>x.observed!==x.expected))throw Error('numeric index synthetic control failed');
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
if(input.schema!=='gamma.current875.ast-inventory-input.v1'||input.fit_problems!==300||input.variants.length!==875)throw Error('fixed875/300 inventory scope required');
const seen=new Set(),owners=new Set();
for(const v of input.variants){
 if(seen.has(v.key)||hash(v.source)!==v.source_sha256)throw Error('source identity drift');seen.add(v.key);owners.add(v.problem_id);
 let row={key:v.key,problem_id:v.problem_id,source_sha256:v.source_sha256,research_candidate:false,qualification:false};
 try{
  const subset=strictSubset(v.source),index=numericIndexProof(v.source),map=resolution(v.source);
  row={...row,static_subset:subset.admitted,rejection_reasons:subset.reasons,index_proof:index,resolution_sha256:hash(JSON.stringify(map)),bindings:map.bindings.length,occurrences:map.occurrences.length,requires_independent_numeric_JSON_domain_review:true};
  row.research_candidate=subset.admitted&&index.all_computed_indices_inductively_numeric;
 }catch(e){row.parse_or_analysis_error=e.name;}
 console.log(JSON.stringify(row));
}
if(owners.size!==300)throw Error('fit owner denominator drift');
console.log(JSON.stringify({done:875,fit_problems:300,candidate_executions:0,transformed_sources_produced:0,qualification:false}));
