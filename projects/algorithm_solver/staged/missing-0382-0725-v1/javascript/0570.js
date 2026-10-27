'use strict';

// 570. Managers with at Least 5 Direct Reports. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. employee: id, name, department, managerId (nullable). Output: name.

function solve(employee) {
  const counts = new Map();
  for (const row of employee) {
    if (row.managerId != null) counts.set(row.managerId, (counts.get(row.managerId) || 0) + 1);
  }
  return employee.filter(row => (counts.get(row.id) || 0) >= 5).map(row => ({name: row.name}));
}

const findManagers = solve;
class Solution {
  findManagers(employee) { return solve(employee); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findManagers };
