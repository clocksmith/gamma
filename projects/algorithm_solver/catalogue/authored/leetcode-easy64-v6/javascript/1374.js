'use strict';

// 1374. Generate a String With Characters That Have Odd Counts (Easy).
// Specification: https://leetcode.com/problems/generate-a-string-with-characters-that-have-odd-counts/description/
// O(n) time and result space; use one odd run or two odd runs.
function solve(n) {
  return n % 2 === 1 ? 'a'.repeat(n) : 'a'.repeat(n - 1) + 'b';
}

const generateTheString = solve;
class Solution {
  generateTheString(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, generateTheString };
