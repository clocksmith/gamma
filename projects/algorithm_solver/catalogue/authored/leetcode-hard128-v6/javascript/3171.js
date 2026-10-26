'use strict';

// 3171. Find Subarray With Bitwise OR Closest to K.
// Maintain the distinct OR values of subarrays ending at each index; O(n*B) expected time and O(B) space. Inputs are preserved.

function solve(nums, k) {
  let ending = new Set(), answer = Infinity;
  for (const value of nums) {
    const following = new Set([value]);
    for (const previous of ending) following.add(previous | value);
    ending = following;
    for (const current of ending) answer = Math.min(answer, Math.abs(current - k));
    if (answer === 0) return 0;
  }
  return answer;
}

const minimumDifference = solve;
class Solution {
  minimumDifference(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumDifference };
