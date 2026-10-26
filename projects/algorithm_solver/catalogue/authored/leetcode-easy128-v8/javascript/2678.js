'use strict';

// 2678. Number of Senior Citizens (Easy).
// Specification: https://leetcode.com/problems/number-of-senior-citizens/description/
// O(n) time, O(1) auxiliary space; the two age digits occupy zero-based positions 11 and 12.
function solve(details) {
  let count = 0;
  for (const detail of details) {
    const age = (detail.charCodeAt(11) - 48) * 10 + detail.charCodeAt(12) - 48;
    if (age > 60) count++;
  }
  return count;
}

const countSeniors = solve;
class Solution {
  countSeniors(details) { return solve(details); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSeniors };
