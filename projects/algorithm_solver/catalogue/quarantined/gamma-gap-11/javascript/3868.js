'use strict';

// 3868. Minimum Cost to Equalize Arrays Using Swaps.
// O(n) expected time and O(n) space; free reordering reduces the problem to even multiplicities and surplus transfers.
function solve(nums1, nums2) {
  const difference = new Map();
  for (const value of nums1) difference.set(value, (difference.get(value) || 0) + 1);
  for (const value of nums2) difference.set(value, (difference.get(value) || 0) - 1);
  let answer = 0;
  for (const count of difference.values()) {
    if (count % 2 !== 0) return -1;
    if (count > 0) answer += count / 2;
  }
  return answer;
}

const minCost = solve;
class Solution {
  minCost(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
