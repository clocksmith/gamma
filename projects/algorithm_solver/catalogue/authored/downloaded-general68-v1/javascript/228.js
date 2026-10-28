'use strict';

// 228. Summary Ranges (Easy).
// Specification: https://leetcode.com/problems/summary-ranges/description/
function solve(nums) {
  const result = [];
  let start = 0;
  for (let i = 0; i < nums.length; i++) {
    if (i + 1 === nums.length || nums[i + 1] !== nums[i] + 1) {
      result.push(start === i ? String(nums[start]) : `${nums[start]}->${nums[i]}`);
      start = i + 1;
    }
  }
  return result;
}
const summaryRanges = solve;
class Solution { summaryRanges(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, summaryRanges };
