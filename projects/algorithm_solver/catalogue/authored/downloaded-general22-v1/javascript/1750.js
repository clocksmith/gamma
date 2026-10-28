'use strict';

// 1750. Minimum Length of String After Deleting Similar Ends (Medium).
// Specification: https://leetcode.com/problems/minimum-length-of-string-after-deleting-similar-ends/description/
function solve(s) {
  let left = 0; let right = s.length - 1;
  while (left < right && s[left] === s[right]) {
    while (left + 1 < right && s[left] === s[left + 1]) left++;
    while (left < right - 1 && s[right - 1] === s[right]) right--;
    left++; right--;
  }
  return Math.max(0, right - left + 1);
}
const minimumLength = solve;
class Solution { minimumLength(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumLength };
