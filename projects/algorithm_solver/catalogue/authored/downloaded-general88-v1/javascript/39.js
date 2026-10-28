'use strict';

// 39. Combination Sum (Medium).
// Specification: https://leetcode.com/problems/combination-sum/description/
function solve(candidates, target) {
  const sorted = candidates.slice().sort((a, b) => a - b);
  const result = [];
  function backtrack(start, remaining, current) {
    if (remaining === 0) { result.push(current.slice()); return; }
    for (let i = start; i < sorted.length; i++) {
      if (sorted[i] > remaining) break;
      current.push(sorted[i]);
      backtrack(i, remaining - sorted[i], current);
      current.pop();
    }
  }
  backtrack(0, target, []);
  return result;
}
const combinationSum = solve;
class Solution { combinationSum(candidates, target) { return solve(candidates, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, combinationSum };
