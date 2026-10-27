'use strict';

// 579. Find Cumulative Salary of an Employee. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. employee: id, month, salary (one year). Output: id, month, Salary. Uses three calendar months, not three observed records; excludes each latest month.

function solve(employee) {
  const groups = new Map();
  for (const row of employee) {
    if (!groups.has(row.id)) groups.set(row.id, new Map());
    groups.get(row.id).set(row.month, row.salary);
  }
  const result = [];
  for (const id of [...groups.keys()].sort((a, b) => a - b)) {
    const months = groups.get(id);
    const ordered = [...months.keys()].sort((a, b) => b - a);
    for (let i = 1; i < ordered.length; i += 1) {
      const month = ordered[i];
      let sum = 0;
      for (let offset = 0; offset < 3; offset += 1) sum += months.get(month - offset) || 0;
      result.push({id, month, Salary: sum});
    }
  }
  return result;
}

const cumulativeSalary = solve;
class Solution {
  cumulativeSalary(employee) { return solve(employee); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, cumulativeSalary };
