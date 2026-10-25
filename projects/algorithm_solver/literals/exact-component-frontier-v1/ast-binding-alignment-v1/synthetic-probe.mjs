// Public fixtures; parser/effect observations only, never evaluate source strings.
import crypto from 'node:crypto';
import {compareResolution,strictSubset,align} from './alignment.mjs';
const controls=[
 ['alpha_parameters','function solve(a,b){return a-b;}','function solve(p0,p1){return p0-p1;}'],
 ['swapped_references','function solve(a,b){return a-b;}','function solve(a,b){return b-a;}'],
 ['shadowed_blocks','function solve(x){let y=x;{let x=3;y+=x;}return y;}','function solve(p0){let v0=p0;{let v1=3;v0+=v1;}return v0;}'],
 ['closure_capture','function solve(x){function inner(y){return x+y;}return x;}','function solve(p0){function inner(p1){return p0+p1;}return p0;}'],
 ['capture_changed','function solve(x){function inner(y){return x+y;}return x;}','function solve(x){function inner(y){return y+y;}return x;}'],
 ['unresolved_global_changed','function solve(x){return external+x;}','function solve(x){return another+x;}'],
 ['unresolved_global_preserved','function solve(x){return external+x;}','function solve(p0){return external+p0;}']
];
for(const[name,before,after]of controls){let mapping_equal=true;try{compareResolution(before,after);}catch{mapping_equal=false;}console.log(JSON.stringify({kind:'mapping',name,mapping_equal}));}
const sources={numeric_loop:'function solve(a){let total=0;for(let i=0;i<a.length;i++){total+=a[i];}return total;}',
 reflection_call:'function solve(a){return String(solve);}',function_coercion:'function solve(a){return solve+0;}',
 computed_name:'function solve(a){let k="name";return solve[k];}',getter:'function solve(a){let o={get x(){return 1;}};return 1;}',
 template:'function solve(a){return `${solve}`;}',global_access:'function solve(a){return external+a;}',
 literal_api:'function solve(a){return a.map;}',callback:'function solve(a){let f=x=>x+1;return 1;}'};
for(const[name,source]of Object.entries(sources)){const r=strictSubset(source);console.log(JSON.stringify({kind:'subset',name,admitted:r.admitted,reasons:r.reasons}));}
const source=sources.numeric_loop,sourceSha256=crypto.createHash('sha256').update(source).digest('hex');
const audit={source_sha256:sourceSha256,independent_review:true,numeric_json_domain:true,numeric_index_bindings:true,no_reflection_review:true};
let aligned=false,bad_hash_rejected=false,missing_audit_rejected=false;
try{aligned=align(source,{audit,sourceSha256}).occurrence_resolution_verified;}catch{}
try{align(source,{audit,sourceSha256:'0'.repeat(64)});}catch{bad_hash_rejected=true;}
try{align(source,{sourceSha256});}catch{missing_audit_rejected=true;}
console.log(JSON.stringify({kind:'alignment',aligned,bad_hash_rejected,missing_audit_rejected}));
console.log(JSON.stringify({done:17}));
