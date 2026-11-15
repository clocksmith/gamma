import assert from 'node:assert/strict';
import {fixture} from './position_balanced_tasks.mjs';
import {assessDiscrimination,selectDonorIndex} from './discrimination.mjs';
const rows=f=>fixture.tasks.map((t,i)=>({task:t[0],arm:'base',predicted:f(t,i)}));
for(let label=0;label<4;label++){
 const outcome=assessDiscrimination(fixture.tasks,rows(()=>label),fixture.baseGate);
 assert.equal(outcome.correct,8);assert.equal(outcome.pass,false);assert.equal(outcome.invariantCases,0);
}
const perfect=assessDiscrimination(fixture.tasks,rows(t=>t[3]),fixture.baseGate);
assert.equal(perfect.correct,32);assert.equal(perfect.pass,false);assert.equal(perfect.invariantCases,8);
const mixed=assessDiscrimination(fixture.tasks,rows((t,i)=>i<24?t[3]:(t[3]+1)%4),fixture.baseGate);
assert.equal(mixed.correct,24);assert.equal(mixed.stableCases,6);assert.equal(mixed.pass,true);
assert.throws(()=>assessDiscrimination(fixture.tasks,[],fixture.baseGate));
console.log('Position gate rejects all four constant letters and ceiling; accepts discriminative mixed control');

for(let i=0;i<fixture.tasks.length;i++) { const donor=selectDonorIndex(fixture.tasks,i); assert.notEqual(fixture.tasks[i][1],fixture.tasks[donor][1]); }
assert.throws(()=>selectDonorIndex(fixture.tasks.slice(0,4),0));
console.log("Donor selection excludes all permutations of the same semantic case");
const expected=['pen','Lynx','maple','Quarry','bonono','starf','box','drum'];
for(let i=0;i<fixture.tasks.length;i++) {
 const task=fixture.tasks[i]; assert.equal(task[2][task[3]], expected[Math.floor(i/4)]);
}
console.log('All thirty-two permuted semantic answer keys verified');
