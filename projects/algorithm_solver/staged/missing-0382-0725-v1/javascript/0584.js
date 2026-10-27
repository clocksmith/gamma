'use strict';

// 584. Find Customer Referee. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. customer: id, name, referee_id (nullable). Output: name; NULL referee_id qualifies.

function solve(customer) {
  return customer.filter(row => row.referee_id !== 2).map(row => ({name: row.name}));
}

const findCustomerReferee = solve;
class Solution {
  findCustomerReferee(customer) { return solve(customer); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findCustomerReferee };
