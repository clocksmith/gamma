import assert from 'node:assert/strict';

// A fresh fixture changes the development population, never the sealed confirmation.
export function validateTasks(tasks) {
  assert.ok(Array.isArray(tasks) && tasks.length >= 2, 'At least two tasks are required for the other-task control');
  const ids = new Set();
  for (const task of tasks) {
    assert.ok(Array.isArray(task) && task.length === 4, 'Expected [id, question, four choices, answer index]');
    const [id, question, choices, answer] = task;
    assert.ok(typeof id === 'string' && id.trim() && !ids.has(id), 'Task IDs must be unique nonempty strings');
    ids.add(id);
    assert.ok(typeof question === 'string' && question.trim(), 'Question must be nonempty');
    assert.ok(Array.isArray(choices) && choices.length === 4 && choices.every(x => typeof x === 'string' && x.trim()), 'Four nonempty string choices required');
    assert.equal(new Set(choices).size, 4, 'Choice strings must be distinct');
    assert.ok(Number.isInteger(answer) && answer >= 0 && answer < 4, 'Answer index must be in [0, 3]');
  }
  return structuredClone(tasks);
}
