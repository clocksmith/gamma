import assert from 'node:assert/strict';
import { validateTasks } from './task_contract.mjs';
const tasks = [['one', 'Q?', ['a','b','c','d'],0], ['two','Q2?', ['a','b','c','d'],3]];
assert.deepEqual(validateTasks(tasks), tasks);
assert.notEqual(validateTasks(tasks)[0], tasks[0]);
for (const invalid of [[], tasks.slice(0,1), [tasks[0],tasks[0]], [tasks[0],['two','Q', ['a','a','c','d'],0]], [tasks[0],['two','Q',['a','b','c','d'],4]], [tasks[0],['two','',['a','b','c','d'],0]]]) {
  assert.throws(() => validateTasks(invalid));
}
console.log('Task contract: valid fixture and six malformed cases passed');
const { tasks: freshTasks } = await import('./fresh_code_tasks.mjs');
assert.deepEqual(freshTasks.map(task => Number(task[2][task[3]])), [40,0,11,48,21,4,10,5,6,4,18,46]);
assert.deepEqual([0,1,2,3].map(index => freshTasks.filter(task => task[3] === index).length), [3,3,3,3]);
console.log('Fresh code fixture: twelve oracle results and balanced labels passed');
