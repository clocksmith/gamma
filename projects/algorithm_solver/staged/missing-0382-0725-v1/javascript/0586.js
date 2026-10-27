'use strict';

// 586. Customer Placing the Largest Number of Orders. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. orders: order_number, customer_number. Output: customer_number. The statement guarantees a unique maximum.

function solve(orders) {
  const counts = new Map();
  for (const row of orders) counts.set(row.customer_number, (counts.get(row.customer_number) || 0) + 1);
  let winner = null;
  for (const [id, count] of counts) {
    if (winner === null || count > counts.get(winner) || (count === counts.get(winner) && id < winner)) winner = id;
  }
  return winner === null ? [] : [{customer_number: winner}];
}

const largestOrderCustomer = solve;
class Solution {
  largestOrderCustomer(orders) { return solve(orders); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestOrderCustomer };
