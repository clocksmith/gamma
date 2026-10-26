'use strict';

// 2570. Merge Two 2D Arrays by Summing Values (Easy).
// Specification: https://leetcode.com/problems/merge-two-2d-arrays-by-summing-values/description/
// O(n + m) time and result space; merge sorted IDs into fresh pairs; preserve inputs and row identities.
function solve(nums1, nums2) {
  const result = [];
  let first = 0;
  let second = 0;
  while (first < nums1.length || second < nums2.length) {
    if (second === nums2.length ||
        (first < nums1.length && nums1[first][0] < nums2[second][0])) {
      result.push([nums1[first][0], nums1[first][1]]);
      first++;
    } else if (first === nums1.length || nums2[second][0] < nums1[first][0]) {
      result.push([nums2[second][0], nums2[second][1]]);
      second++;
    } else {
      result.push([nums1[first][0], nums1[first][1] + nums2[second][1]]);
      first++;
      second++;
    }
  }
  return result;
}

const mergeArrays = solve;
class Solution {
  mergeArrays(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mergeArrays };
