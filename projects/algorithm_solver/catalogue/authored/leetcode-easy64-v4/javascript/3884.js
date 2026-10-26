'use strict';

// 3884. First Matching Character From Both Ends (Easy).
// Specification: https://leetcode.com/problems/first-matching-character-from-both-ends/description/
// O(n) time, O(1) space; include the center character when the length is odd.
function solve(s) {
  let left = 0;
  let right = s.length - 1;
  while (left <= right) {
    if (s[left] === s[right]) return left;
    left++;
    right--;
  }
  return -1;
}

const firstMatchingIndex = solve;
class Solution {
  firstMatchingIndex(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, firstMatchingIndex };
