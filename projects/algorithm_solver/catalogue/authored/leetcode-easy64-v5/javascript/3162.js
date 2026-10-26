'use strict';

// 3162. Find the Number of Good Pairs I (Easy).
// Specification: https://leetcode.com/problems/find-the-number-of-good-pairs-i/description/
// O(n * m) time, O(1) auxiliary space; all divisors are positive; preserve arrays.
function solve(nums1, nums2, k) {
  let pairs = 0;
  for (const first of nums1) {
    for (const second of nums2) {
      if (first % (second * k) === 0) pairs++;
    }
  }
  return pairs;
}

const numberOfPairs = solve;
class Solution {
  numberOfPairs(nums1, nums2, k) { return solve(nums1, nums2, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfPairs };
