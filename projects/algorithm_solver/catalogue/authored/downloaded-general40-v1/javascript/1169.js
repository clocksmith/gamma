'use strict';

// 1169. Invalid Transactions (Medium).
// Specification: https://leetcode.com/problems/invalid-transactions/description/
function parse(text) {
  const parts = text.split(',');
  return { name: parts[0], time: Number(parts[1]), amount: Number(parts[2]), city: parts[3] };
}
function solve(transactions) {
  const parsed = transactions.map(parse);
  const result = [];
  for (let i = 0; i < transactions.length; i++) {
    let invalid = parsed[i].amount > 1000;
    if (!invalid) {
      for (let j = 0; j < transactions.length; j++) {
        if (i !== j && parsed[j].name === parsed[i].name && parsed[j].city !== parsed[i].city && Math.abs(parsed[j].time - parsed[i].time) <= 60) { invalid = true; break; }
      }
    }
    if (invalid) result.push(transactions[i]);
  }
  return result;
}
const invalidTransactions = solve;
class Solution { invalidTransactions(transactions) { return solve(transactions); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, invalidTransactions };
