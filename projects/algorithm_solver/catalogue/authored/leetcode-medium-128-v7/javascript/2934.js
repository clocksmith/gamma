'use strict';

// 2934. Minimum Operations to Maximize Last Elements in Arrays: compare keeping and swapping the last pair while independently fitting every earlier pair.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums1, nums2) {
  function needed(first, second) {
    let swaps = 0;
    for (let index = 0; index + 1 < nums1.length; index += 1) {
      const left = nums1[index];
      const right = nums2[index];
      if (left <= first && right <= second) continue;
      if (right > first || left > second) return nums1.length + 1;
      swaps += 1;
    }
    return swaps;
  }
  const last = nums1.length - 1;
  const best = Math.min(needed(nums1[last], nums2[last]), 1 + needed(nums2[last], nums1[last]));
  return best <= nums1.length ? best : -1;
}

const minOperations = solve;
class Solution {
  minOperations(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
