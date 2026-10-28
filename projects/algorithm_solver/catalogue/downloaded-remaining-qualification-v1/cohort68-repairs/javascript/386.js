'use strict';

// 386. Lexicographical Numbers (Medium).
// Specification: https://leetcode.com/problems/lexicographical-numbers/description/
function solve(n) {
  const result = [];
  let current = 1;
  for (let i = 0; i < n; i++) {
    result.push(current);
    if (current * 10 <= n) current *= 10;
    else {
      while (current % 10 === 9 || current + 1 > n) current = Math.floor(current / 10);
      current++;
    }
  }
  return result;
}
const lexicalOrder = solve;
class Solution { lexicalOrder(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, lexicalOrder };
