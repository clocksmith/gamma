'use strict';

// Only arguments enter this process; all expected answers stay in the Python parent.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
if (![802, 871, 875, 1438, 1547, 2246, 2406, 2416].includes(request.id)) {
  throw new Error('Problem outside this batch');
}
const source = fs.readFileSync(path.join(__dirname, 'javascript', `${request.id}.js`), 'utf8');
const context = { module: { exports: {} } };
vm.runInNewContext(source, context, { filename: `${request.id}.js`, timeout: 1000 });
const solution = context.module.exports;
const instance = new solution.Solution();
const methods = [solution.solve, args => instance[request.method](...args), solution[request.method]];
function containers(value, found = new Set()) {
  if (value !== null && typeof value === 'object' && !found.has(value)) {
    found.add(value);
    for (const child of Object.values(value)) containers(child, found);
  }
  return found;
}
function checkResult(value) {
  if (Array.isArray(value)) {
    for (const child of value) checkResult(child);
  } else if (!Number.isSafeInteger(value)) throw new Error('Result is not an exact safe integer');
}
const results = request.cases.map(original => {
  const values = methods.map((method, index) => {
    const args = structuredClone(original);
    const result = index === 1 ? method(args) : method(...args);
    assert.deepEqual(args, original, 'Input mutated');
    const owned = containers(args);
    for (const value of containers(result)) assert(!owned.has(value), 'Output aliases input');
    checkResult(result);
    return JSON.parse(JSON.stringify(result));
  });
  assert.deepEqual(values[0], values[1], 'Solution wrapper drift');
  assert.deepEqual(values[0], values[2], 'LeetCode function alias drift');
  return values[0];
});
process.stdout.write(JSON.stringify(results));
