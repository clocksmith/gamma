'use strict';

// 1736. Latest Time by Replacing Hidden Digits (Easy).
// Specification: https://leetcode.com/problems/latest-time-by-replacing-hidden-digits/description/
// O(1) time and space for the fixed five-character 24-hour time.
function solve(time) {
  const result = time.split('');
  if (result[0] === '?') result[0] = result[1] === '?' || result[1] <= '3' ? '2' : '1';
  if (result[1] === '?') result[1] = result[0] === '2' ? '3' : '9';
  if (result[3] === '?') result[3] = '5';
  if (result[4] === '?') result[4] = '9';
  return result.join('');
}

const maximumTime = solve;
class Solution {
  maximumTime(time) { return solve(time); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumTime };
