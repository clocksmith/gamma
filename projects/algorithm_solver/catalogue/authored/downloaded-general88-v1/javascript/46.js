'use strict';

// 46. Permutations (Medium).
// Specification: https://leetcode.com/problems/permutations/description/
function solve(nums) {
  const result = [];
  function backtrack(current, remaining) {
    if (remaining.length === 0) { result.push(current.slice()); return; }
    for (let i = 0; i < remaining.length; i++) {
      current.push(remaining[i]);
      backtrack(current, remaining.slice(0, i).concat(remaining.slice(i + 1)));
      current.pop();
    }
  }
  backtrack([], nums.slice());
  return result;
}
const permute = solve;
class Solution { permute(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, permute };
