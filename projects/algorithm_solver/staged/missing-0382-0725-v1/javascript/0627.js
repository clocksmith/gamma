'use strict';

// 627. Swap Salary. Gamma row-record adapter for a SQL UPDATE, not a native SQL submission. salary rows have id, name, sex, salary. Mutates each original row sex in place and returns the original table; other columns and row identities are preserved.

function solve(salary) {
  for (const row of salary) {
    if (row.sex === 'm') row.sex = 'f';
    else if (row.sex === 'f') row.sex = 'm';
  }
  return salary;
}

const swapSalary = solve;
class Solution {
  swapSalary(salary) { return solve(salary); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, swapSalary };
