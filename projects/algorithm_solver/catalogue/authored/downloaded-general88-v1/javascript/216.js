'use strict';

// 216. Combination Sum III (Medium).
// Specification: https://leetcode.com/problems/combination-sum-iii/description/
function solve(k, n) {
  const result = [];
  function backtrack(start, remaining, current) {
    if (current.length === k) { if (remaining === 0) result.push(current.slice()); return; }
    for (let value = start; value <= 9; value++) {
      if (value > remaining) break;
      current.push(value); backtrack(value + 1, remaining - value, current); current.pop();
    }
  }
  backtrack(1, n, []);
  return result;
}
const combinationSum3 = solve;
class Solution { combinationSum3(k, n) { return solve(k, n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, combinationSum3 };
