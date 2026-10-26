'use strict';

// 1221. Split a String in Balanced Strings (Easy).
// Specification: https://leetcode.com/problems/split-a-string-in-balanced-strings/description/
// O(n) time, O(1) space; split at every zero balance.
function solve(s) {
  let balance = 0;
  let result = 0;
  for (const character of s) {
    balance += character === 'L' ? 1 : -1;
    if (balance === 0) result++;
  }
  return result;
}

const balancedStringSplit = solve;
class Solution {
  balancedStringSplit(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, balancedStringSplit };
