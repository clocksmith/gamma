'use strict';

// 3019. Number of Changing Keys (Easy).
// Specification: https://leetcode.com/problems/number-of-changing-keys/description/
// O(n) time, O(1) auxiliary space; compare neighboring ASCII letters case-insensitively.
function solve(s) {
  let result = 0;
  for (let index = 1; index < s.length; index++) {
    if (s[index].toLowerCase() !== s[index - 1].toLowerCase()) result++;
  }
  return result;
}

const countKeyChanges = solve;
class Solution {
  countKeyChanges(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countKeyChanges };
