'use strict';

// 1332. Remove Palindromic Subsequences (Easy).
// Specification: https://leetcode.com/problems/remove-palindromic-subsequences/description/
function solve(s) {
  if (s.length === 0) return 0;
  if (s === s.split("").reverse().join("")) return 1;
  return 2;
}
const removePalindromeSub = solve;
class Solution { removePalindromeSub(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, removePalindromeSub };
