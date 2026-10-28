'use strict';

// 386. Lexicographical Numbers (Medium).
// Specification: https://leetcode.com/problems/lexicographical-numbers/description/
function solve(n) {
  const result = [];
  for (let value = 1; value <= n; value++) result.push(value);
  result.sort((a, b) => String(a).localeCompare(String(b)));
  return result;
}
const lexicalOrder = solve;
class Solution { lexicalOrder(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, lexicalOrder };
