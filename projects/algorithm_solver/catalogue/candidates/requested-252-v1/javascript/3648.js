'use strict';

// 3648. Minimum Sensors to Cover Grid.
// Specification: https://leetcode.com/problems/minimum-sensors-to-cover-grid/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(1) time and space; each sensor covers Chebyshev distance at most k.
// Inputs are not modified.

function solve(n, m, k) {
  const width = 2 * k + 1;
  return Math.ceil(n / width) * Math.ceil(m / width);
}

const minSensors = solve;
class Solution {
  minSensors(n, m, k) { return solve(n, m, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSensors };
