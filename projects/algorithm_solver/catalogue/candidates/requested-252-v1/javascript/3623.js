'use strict';

// 3623. Count Number of Trapezoids I.
// Specification: https://leetcode.com/problems/count-number-of-trapezoids-i/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(n) expected time and space; horizontal trapezoids from pairs on distinct y levels.
// Inputs are not modified.

function solve(points) {
  const levels = new Map();
  for (const [x, y] of points) levels.set(y, (levels.get(y) || 0) + 1);
  let previous = 0n, answer = 0n;
  for (const count of levels.values()) {
    const pairs = BigInt(count) * BigInt(count - 1) / 2n;
    answer = (answer + previous * pairs) % 1000000007n;
    previous = (previous + pairs) % 1000000007n;
  }
  return Number(answer);
}

const countTrapezoids = solve;
class Solution {
  countTrapezoids(points) { return solve(points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countTrapezoids };
