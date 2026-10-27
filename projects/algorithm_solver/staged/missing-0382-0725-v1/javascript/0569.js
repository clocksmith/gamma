'use strict';

// 569. Median Employee Salary. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. employee: id, company, salary. Output retains one or two middle employee rows per company, breaking equal salaries by id.

function solve(employee) {
  const groups = new Map();
  for (const row of employee) {
    if (!groups.has(row.company)) groups.set(row.company, []);
    groups.get(row.company).push(row);
  }
  const result = [];
  for (const company of [...groups.keys()].sort()) {
    const rows = groups.get(company).sort((a, b) => a.salary - b.salary || a.id - b.id);
    for (let i = Math.floor((rows.length - 1) / 2); i <= Math.floor(rows.length / 2); i += 1) {
      result.push({id: rows[i].id, company, salary: rows[i].salary});
    }
  }
  return result;
}

const medianEmployeeSalary = solve;
class Solution {
  medianEmployeeSalary(employee) { return solve(employee); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, medianEmployeeSalary };
