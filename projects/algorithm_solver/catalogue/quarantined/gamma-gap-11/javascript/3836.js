'use strict';

// 3836. Maximum Score Using Exactly K Pairs.
// O(n m k) time and O(m k) space; exact-count ordered-pair DP, including mandatory negative scores.
function solve(nums1, nums2, k) {
  const m = nums2.length;
  let previous = Array.from({ length: k + 1 }, () => Array(m + 1).fill(-Infinity));
  previous[0].fill(0);
  for (let length = 1; length <= nums1.length; length += 1) {
    const current = previous.map(row => row.slice());
    for (let index = 1; index <= m; index += 1) {
      const product = nums1[length - 1] * nums2[index - 1];
      for (let count = 1; count <= Math.min(length, index, k); count += 1) {
        current[count][index] = Math.max(previous[count][index], current[count][index - 1], previous[count - 1][index - 1] + product);
      }
    }
    previous = current;
  }
  return previous[k][m];
}

const maxScore = solve;
class Solution {
  maxScore(nums1, nums2, k) { return solve(nums1, nums2, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScore };
