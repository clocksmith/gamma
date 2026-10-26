'use strict';

// 2839. Check if Strings Can be Made Equal With Operations I (Easy).
// Specification: https://leetcode.com/problems/check-if-strings-can-be-made-equal-with-operations-i/description/
// O(1) time and space for strings of length four; preserve both strings.
function solve(s1, s2) {
  for (let offset = 0; offset < 2; offset++) {
    const unchanged = s1[offset] === s2[offset] && s1[offset + 2] === s2[offset + 2];
    const swapped = s1[offset] === s2[offset + 2] && s1[offset + 2] === s2[offset];
    if (!unchanged && !swapped) return false;
  }
  return true;
}

const canBeEqual = solve;
class Solution {
  canBeEqual(s1, s2) { return solve(s1, s2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canBeEqual };
