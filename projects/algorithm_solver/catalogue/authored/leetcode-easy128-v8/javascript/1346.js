'use strict';

// 1346. Check If N and Its Double Exist (Easy).
// Specification: https://leetcode.com/problems/check-if-n-and-its-double-exist/description/
// O(n) expected time, O(n) space; query only earlier elements so indices remain distinct.
function solve(arr) {
  const seen = new Set();
  for (const value of arr) {
    if (seen.has(2 * value) || (value % 2 === 0 && seen.has(value / 2))) return true;
    seen.add(value);
  }
  return false;
}

const checkIfExist = solve;
class Solution {
  checkIfExist(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkIfExist };
