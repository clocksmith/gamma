'use strict';

// 690. Employee Importance. Read Employee objects (or equivalent records) and count each reachable employee once.

function solve(employees, id) {
  const byId = new Map(employees.map(employee => [employee.id, employee])), stack = [id], seen = new Set();
  let answer = 0;
  while (stack.length > 0) {
    const identifier = stack.pop();
    if (seen.has(identifier)) continue;
    seen.add(identifier);
    const employee = byId.get(identifier);
    answer += employee.importance;
    for (const subordinate of employee.subordinates) stack.push(subordinate);
  }
  return answer;
}

const getImportance = solve;
class Solution {
  getImportance(employees, id) { return solve(employees, id); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getImportance };
