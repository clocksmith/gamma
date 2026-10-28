'use strict';

// 2330. Valid Palindrome IV (Medium).
// Specification: https://leetcode.com/problems/valid-palindrome-iv/description/
function solve(s) {
  let mismatches = 0;
  let l = 0; let r = s.length - 1;
  while (l < r) {
    if (s[l] !== s[r]) mismatches++;
    l++; r--;
  }
  return mismatches <= 2;
}
const makePalindrome = solve;
class Solution { makePalindrome(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, makePalindrome };
