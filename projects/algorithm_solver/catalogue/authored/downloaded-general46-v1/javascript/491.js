'use strict';

// 491. Non-decreasing Subsequences (Medium).
// Specification: https://leetcode.com/problems/non-decreasing-subsequences/description/
function solve(nums) {
  const seen = new Set();
  const result = [];
  function backtrack(start, current) {
    if (current.length >= 2) {
      const key = current.join(',');
      if (!seen.has(key)) { seen.add(key); result.push(current.slice()); }
    }
    for (let i = start; i < nums.length; i++) {
      if (current.length === 0 || nums[i] >= current[current.length - 1]) { current.push(nums[i]); backtrack(i + 1, current); current.pop(); }
    }
  }
  backtrack(0, []);
  result.sort((a, b) => {
    const textA = a.join(','); const textB = b.join(',');
    return textA < textB ? -1 : textA > textB ? 1 : 0;
  });
  return result;
}
const findSubsequences = solve;
class Solution { findSubsequences(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findSubsequences };
