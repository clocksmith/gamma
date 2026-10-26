'use strict';

// 744. Find Smallest Letter Greater Than Target (Easy).
// Specification: https://leetcode.com/problems/find-smallest-letter-greater-than-target/description/
// O(log n) time, O(1) space; upper-bound search with circular wraparound.
function solve(letters, target) {
  let left = 0;
  let right = letters.length;
  while (left < right) {
    const middle = left + Math.floor((right - left) / 2);
    if (letters[middle] <= target) left = middle + 1;
    else right = middle;
  }
  return letters[left % letters.length];
}

const nextGreatestLetter = solve;
class Solution {
  nextGreatestLetter(letters, target) { return solve(letters, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, nextGreatestLetter };
