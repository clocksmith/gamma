'use strict';

// 1317. Convert Integer to the Sum of Two No-Zero Integers (Easy).
// Specification: https://leetcode.com/problems/convert-integer-to-the-sum-of-two-no-zero-integers/description/
// O(n log n) time, O(1) auxiliary space. Choose the first valid positive pair.
function solve(n) {
  function hasZero(value) {
    while (value > 0) {
      if (value % 10 === 0) return true;
      value = Math.floor(value / 10);
    }
    return false;
  }

  for (let first = 1; first < n; first++) {
    const second = n - first;
    if (!hasZero(first) && !hasZero(second)) return [first, second];
  }
  return [];
}

const getNoZeroIntegers = solve;
class Solution {
  getNoZeroIntegers(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getNoZeroIntegers };
