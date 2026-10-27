'use strict';

// 607. Sales Person. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. sales_person: sales_id, name, salary, commission_rate, hire_date; company: com_id, name, city; orders: order_id, order_date, com_id, sales_id, amount. Output: name.

function solve(sales_person, company, orders) {
  const red = new Set(company.filter(row => row.name === 'RED').map(row => row.com_id));
  const excluded = new Set(orders.filter(row => red.has(row.com_id)).map(row => row.sales_id));
  return sales_person.filter(row => !excluded.has(row.sales_id)).map(row => ({name: row.name}));
}

const salesPerson = solve;
class Solution {
  salesPerson(sales_person, company, orders) { return solve(sales_person, company, orders); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, salesPerson };
