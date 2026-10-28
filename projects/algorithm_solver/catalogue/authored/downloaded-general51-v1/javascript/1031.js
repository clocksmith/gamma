'use strict';

// 1031. Maximum Sum of Two Non-Overlapping Subarrays (Medium).
// Specification: https://leetcode.com/problems/maximum-sum-of-two-non-overlapping-subarrays/description/
function solve(nums, firstLen, secondLen) {
  const prefix = [0];
  for (const value of nums) prefix.push(prefix[prefix.length - 1] + value);
  function subarraySum(start, length) { return prefix[start + length] - prefix[start]; }
  let best = -Infinity;
  for (let i = 0; i + firstLen <= nums.length; i++) {
    for (let j = 0; j + secondLen <= nums.length; j++) {
      if (i + firstLen <= j || j + secondLen <= i) best = Math.max(best, subarraySum(i, firstLen) + subarraySum(j, secondLen));
    }
  }
  return best;
}
const maxSumTwoNoOverlap = solve;
class Solution { maxSumTwoNoOverlap(nums, firstLen, secondLen) { return solve(nums, firstLen, secondLen); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSumTwoNoOverlap };
