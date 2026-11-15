import assert from 'node:assert/strict';

export function assessDiscrimination(tasks, rows, gate) {
  assert.equal(tasks.length,32,'The preregistered gate requires eight cases and four permutations');
  const byId=new Map(rows.filter(x=>x.arm==='base').map(x=>[x.task,x]));
  assert.equal(byId.size,tasks.length);
  const labelCounts=[0,0,0,0], cases=new Map();
  let correct=0;
  for(const [id,,choices,answer] of tasks){
    const row=byId.get(id);assert.ok(row && Number.isInteger(row.predicted) && row.predicted>=0 && row.predicted<4);
    const match=/^(.*)-p([0-3])$/.exec(id);assert.ok(match);
    const state=cases.get(match[1])??{permutations:new Set(),correct:0,answers:new Set()};
    assert.ok(!state.permutations.has(match[2]));state.permutations.add(match[2]);
    state.correct+=Number(row.predicted===answer);state.answers.add(choices[row.predicted]);
    cases.set(match[1],state);labelCounts[row.predicted]++;correct+=Number(row.predicted===answer);
  }
  assert.equal(cases.size,8);assert.ok([...cases.values()].every(x=>x.permutations.size===4));
  const stableCases=[...cases.values()].filter(x=>x.correct>=3).length;
  const invariantCases=[...cases.values()].filter(x=>x.answers.size===1).length;
  const modalLabelCount=Math.max(...labelCounts);
  return {correct,count:tasks.length,labelCounts,stableCases,invariantCases,modalLabelCount,
    pass:correct>=gate.minimumCorrect && correct<=gate.maximumCorrect && stableCases>=gate.minimumStableCases && modalLabelCount<=gate.maximumModalLabelCount};
}

export function selectDonorIndex(tasks, index) {
  assert.ok(Number.isInteger(index) && index >= 0 && index < tasks.length);
  for(let distance=1;distance<tasks.length;distance++){
    const candidate=(index+distance)%tasks.length;
    if(tasks[candidate][1]!==tasks[index][1])return candidate;
  }
  throw new Error('Other-task control requires a different semantic question');
}
