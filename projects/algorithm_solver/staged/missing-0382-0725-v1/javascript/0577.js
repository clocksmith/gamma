'use strict';

// 577. Employee Bonus. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. employee: empId, name, supervisor, salary; bonus: empId, bonus. Output: name, bonus; missing bonuses remain NULL.

function solve(employee, bonus) {
  const bonuses = new Map(bonus.map(row => [row.empId, row.bonus]));
  const result = [];
  for (const row of employee) {
    const value = bonuses.get(row.empId) ?? null;
    if (value === null || value < 1000) result.push({name: row.name, bonus: value});
  }
  return result;
}

const employeeBonus = solve;
class Solution {
  employeeBonus(employee, bonus) { return solve(employee, bonus); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, employeeBonus };
