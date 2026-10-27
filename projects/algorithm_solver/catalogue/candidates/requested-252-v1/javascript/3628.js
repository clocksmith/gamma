'use strict';

// 3628. Maximum Number of Subsequences After One Inserting.
// Specification: https://leetcode.com/problems/maximum-number-of-subsequences-after-one-inserting/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(n) time, O(1) space; count LCT subsequences and the best insertion of L, C, or T.
// Inputs are not modified.

function solve(s) {
  let leftCount = 0, leftCenter = 0, original = 0, centerRight = 0, rightCount = 0;
  for (const character of s) {
    if (character === 'L') leftCount++;
    else if (character === 'C') leftCenter += leftCount;
    else if (character === 'T') original += leftCenter;
  }
  for (let index = s.length - 1; index >= 0; index--) {
    if (s[index] === 'T') rightCount++;
    else if (s[index] === 'C') centerRight += rightCount;
  }
  let bestCenter = 0, left = 0, right = rightCount;
  for (const character of s) {
    bestCenter = Math.max(bestCenter, left * right);
    if (character === 'L') left++;
    else if (character === 'T') right--;
  }
  bestCenter = Math.max(bestCenter, left * right);
  return original + Math.max(leftCenter, centerRight, bestCenter);
}

const numOfSubsequences = solve;
class Solution {
  numOfSubsequences(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numOfSubsequences };
