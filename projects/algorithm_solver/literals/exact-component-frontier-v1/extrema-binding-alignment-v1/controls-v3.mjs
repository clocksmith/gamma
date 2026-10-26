// Independently authored public source strings, parsed but NEVER evaluated.
import crypto from 'node:crypto';import {extremaSubset,alignExtrema}from './alignment-v3.mjs';
const fixtures=[
 ['conditional_test_update','function solve(a){return Math.max(a++ ? 1 : 2,3);}',false],
 ['member_receiver_assignment','function solve(a,b){return Math.max((a=b)[0],1);}',false],
 ['conditional_test_assignment','function solve(a){return Math.max((a=1) ? 1 : 2,3);}',false],
 ['index_update','function solve(a){var i=0;return Math.max(a[i++],1);}',false],
 ['numeric_comparison_condition','function solve(a,b){return Math.max(a>0 ? a : b,3);}',true],
 ['boolean_condition','function solve(a,b){return Math.max(true ? a : b,3);}',true],
 ['nested_numeric_array','function solve(a){return Math.max(a[0][1],1);}',true],
 ['optional_member','function solve(a){return Math?.max(a,1);}',false],
 ['optional_call','function solve(a){return Math.max?.(a,1);}',false],
 ['direct_max','function solve(a,b){return Math.max(a,b);}',true],
 ['nested_extrema','function solve(a,b){return Math.max(a,Math.min(a,b));}',true],
 ['signed_zero','function solve(a){return Math.min(-0,a);}',true],
 ['division_special','function solve(a){return Math.max(a,1/0);}',true],
 ['shadow_param','function solve(Math){return Math.max(1,2);}',false],
 ['shadow_local','function solve(a){var Math=a;return Math.max(1,2);}',false],
 ['mutated_method','function solve(a){Math.max=a;return Math.max(1,2);}',false],
 ['method_alias','function solve(a){var m=Math.max;return m(a,1);}',false],
 ['object_alias','function solve(a){var m=Math;return Math.max(a,1);}',false],
 ['computed_method','function solve(a){return Math["max"](a,1);}',false],
 ['coercion_literal','function solve(a){return Math.max("1",a);}',false],
 ['coercion_array','function solve(a){return Math.max([1],a);}',false],
 ['coercion_object','function solve(a){return Math.max({},a);}',false],
 ['callback','function solve(a){return Math.max(function(){},a);}',false],
 ['getter','function solve(a){var x={get n(){return 1}};return Math.max(x.n,a);}',false],
 ['prototype','function solve(a){a.__proto__=a;return Math.max(1,2);}',false],
 ['indirect','function solve(a){return Math.max.call(null,a,1);}',false],
 ['spread','function solve(a){return Math.max(...a);}',false],
 ['side_effect_argument_order','function solve(a,b){return Math.max(a++,b++);}',false],
 ['boolean_coercion','function solve(a){return Math.max(true,a);}',false],
 ['empty_extrema','function solve(a){return Math.max();}',false],
 ['nonextrema','function solve(a){return Math.floor(a);}',false],
 ['unknown_argument_call','function solve(a){return Math.max(a(),1);}',false],
 ['member_mutation','function solve(a){a[0]=1;return Math.max(a[0],2);}',false],
 ['conditional_index','function solve(a){if(a[0]){var i=0;}return Math.max(a[i],2);}',false],
 ['primitive_argument_audit_required','function solve(a){return Math.max(a,1);}',true]
];
const results=fixtures.map(([name,source,expected])=>({name,expected,observed:extremaSubset(source).syntactic_candidate}));
const source='function solve(a,b){var x=a+b;return Math.max(x,b);}';const sourceSha256=crypto.createHash('sha256').update(source).digest('hex');
let blocked=false;try{alignExtrema(source,{sourceSha256,audit:{source_sha256:sourceSha256}});}catch{blocked=true;}results.push({name:'missing_argument_runtime_proof_blocks_transform',expected:true,observed:blocked});
// Synthetic proof tokens test plumbing only, not a corpus admission receipt.
const audit={source_sha256:sourceSha256,cases_sha256:'0'.repeat(64),effects_sha256:'1'.repeat(64),runtime_sha256:'2'.repeat(64),independent_review:true,finite_contract_numeric_arguments:true,numeric_index_and_array_access_review:true,no_reflection_or_coercion:true,fresh_unmodified_intrinsics:true};
for(const mode of ['format','role']){const t=alignExtrema(source,{sourceSha256,audit,mode});results.push({name:'synthetic_'+mode+'_stable_resolution',expected:true,observed:t.occurrence_resolution_verified&&t.qualification===false});}
console.log(JSON.stringify({controls:results,candidate_execution:false}));if(results.some(x=>x.observed!==x.expected))throw Error('extrema control failure');
