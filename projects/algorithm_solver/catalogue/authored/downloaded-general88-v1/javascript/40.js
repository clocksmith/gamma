'use strict';

// 40. Combination Sum II (Medium).
// Specification: https://leetcode.com/problems/combination-sum-ii/description/
function solve(candidates, target) {
  const sorted = candidates.slice().sort((a, b) => a - b);
  const result = [];
  function backtrack(start, remaining, current) {
    if (remaining === 0) { result.push(current.slice()); return; }
    for (let i = start; i < sorted.length; i++) {
      if (i > start && sorted[i] === sorted[i - 1]) continue;
      if (sorted[i] > remaining) break;
      current.push(sorted[i]);
      backtrack(i + 1, remaining - sorted[i], current);
      current.pop();
    }
  }
  backtrack(0, target, []);
  return result;
}
const combinationSum2 = solve;
class Solution { combinationSum2(candidates, target) { return solve(candidates, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, combinationSum2 };
