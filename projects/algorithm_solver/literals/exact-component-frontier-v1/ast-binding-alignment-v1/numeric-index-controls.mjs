import {numericIndexProof} from './numeric-index-proof.mjs';
export function controls(){
 const rows=[
 ['loop_counter','function solve(a){let z=0;for(let i=0;i<a.length;i++){z+=a[i];}return z;}',true],
 ['parameter_index','function solve(a,i){return a[i];}',false],
 ['unknown_initializer','function solve(a,n){let i=n;return a[i];}',false],
 ['unknown_write','function solve(a,n){let i=0;i=n;return a[i];}',false],
 ['numeric_reassignment','function solve(a){let i=0;i=i+1;return a[i];}',true],
 ['preinitialization_read','function solve(a){let x=a[i];var i=0;return x;}',false],
 ['mutual_numeric_invariant','function solve(a){let i=0;let j=1;i=j+1;j=i*2;return a[i]+a[j];}',true],
 ['unknown_dependency','function solve(a,n){let i=0;let j=1;j=n;i=j;return a[i];}',false],
 ['literal_index','function solve(a){return a[0];}',true]
 ];
 return rows.map(([name,source,expected])=>({name,observed:numericIndexProof(source).all_computed_indices_inductively_numeric,expected}));
}
