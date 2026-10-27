'use strict';

// 615. Average Salary: Departments VS Company. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. salary: id, employee_id, amount (integer), pay_date (YYYY-MM-DD or YYYY/MM/DD); employee: employee_id, department_id. Output: pay_month, department_id, comparison. Compares exact cross-products instead of rounded averages.

function solve(salary, employee) {
  const department = new Map(employee.map(row => [row.employee_id, row.department_id]));
  const company = new Map();
  const groups = new Map();
  for (const row of salary) {
    const month = row.pay_date.replaceAll('/', '-').slice(0, 7);
    const dept = department.get(row.employee_id);
    const key = JSON.stringify([month, dept]);
    if (!company.has(month)) company.set(month, [0n, 0n]);
    if (!groups.has(key)) groups.set(key, {month, dept, sum: 0n, count: 0n});
    if (row.amount != null) {
      const total = company.get(month);
      total[0] += BigInt(row.amount);
      total[1] += 1n;
      const group = groups.get(key);
      group.sum += BigInt(row.amount);
      group.count += 1n;
    }
  }
  return [...groups.values()].sort((a, b) => (a.month < b.month ? -1 : a.month > b.month ? 1 : a.dept - b.dept)).map(group => {
    const [total, count] = company.get(group.month);
    const difference = group.sum * count - total * group.count;
    const comparison = group.count === 0n || count === 0n || difference === 0n ? 'same' : difference > 0n ? 'higher' : 'lower';
    return {pay_month: group.month, department_id: group.dept, comparison};
  });
}

const averageSalary = solve;
class Solution {
  averageSalary(salary, employee) { return solve(salary, employee); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, averageSalary };
