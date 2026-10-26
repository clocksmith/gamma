'use strict';

// 2124. Check if All A's Appears Before All B's (Easy).
// Specification: https://leetcode.com/problems/check-if-all-as-appears-before-all-bs/description/
// O(n) time, O(1) space; reject an a after any b.
function solve(s) {
  let seenB = false;
  for (const character of s) {
    if (character === 'b') seenB = true;
    else if (seenB) return false;
  }
  return true;
}

const checkString = solve;
class Solution {
  checkString(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkString };
