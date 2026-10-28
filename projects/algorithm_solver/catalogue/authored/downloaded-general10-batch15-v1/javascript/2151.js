'use strict';

// 2151. Maximum Good People Based on Statements (Hard).
// Specification: https://leetcode.com/problems/maximum-good-people-based-on-statements/description/
function solve(statements) {
  const n = statements.length;
  let best = 0;
  for (let mask = 0; mask < (1 << n); mask++) {
    const good = [];
    let count = 0;
    for (let i = 0; i < n; i++) {
      const value = (mask >> i) & 1;
      good.push(value);
      count += value;
    }
    let valid = true;
    for (let i = 0; i < n && valid; i++) {
      if (!good[i]) continue;
      for (let j = 0; j < n; j++) {
        if (statements[i][j] !== 2 && statements[i][j] !== good[j]) { valid = false; break; }
      }
    }
    if (valid) best = Math.max(best, count);
  }
  return best;
}
const maximumGood = solve;
class Solution { maximumGood(statements) { return solve(statements); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumGood };
