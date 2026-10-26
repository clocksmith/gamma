'use strict';

// 1855. Maximum Distance Between a Pair of Values: advance monotone pointers while respecting the index ordering.
// O(len(nums1) + len(nums2)) time and O(1) auxiliary space; inputs are read-only.
function solve(nums1, nums2) {
  let left = 0;
  let right = 0;
  let best = 0;
  while (left < nums1.length && right < nums2.length) {
    if (right < left) {
      right = left;
      continue;
    }
    if (nums1[left] <= nums2[right]) {
      best = Math.max(best, right - left);
      right += 1;
    } else {
      left += 1;
    }
  }
  return best;
}

const maxDistance = solve;
class Solution {
  maxDistance(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDistance };
