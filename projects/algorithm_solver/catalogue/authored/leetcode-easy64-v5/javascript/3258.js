'use strict';

// 3258. Count Substrings That Satisfy K-Constraint I (Easy).
// Specification: https://leetcode.com/problems/count-substrings-that-satisfy-k-constraint-i/description/
// O(n) time, O(1) auxiliary space; a window is invalid only when both counts exceed k.
function solve(s, k) {
  let zeros = 0;
  let ones = 0;
  let left = 0;
  let total = 0;
  for (let right = 0; right < s.length; right++) {
    if (s[right] === '0') zeros++;
    else ones++;
    while (zeros > k && ones > k) {
      if (s[left] === '0') zeros--;
      else ones--;
      left++;
    }
    total += right - left + 1;
  }
  return total;
}

const countKConstraintSubstrings = solve;
class Solution {
  countKConstraintSubstrings(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countKConstraintSubstrings };
