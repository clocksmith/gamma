'use strict';

// 264. Ugly Number II (Medium).
// Specification: https://leetcode.com/problems/ugly-number-ii/description/
function solve(n) {
  const ugly = [1];
  let i2 = 0; let i3 = 0; let i5 = 0;
  while (ugly.length < n) {
    const next = Math.min(ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5);
    ugly.push(next);
    if (next === ugly[i2] * 2) i2++;
    if (next === ugly[i3] * 3) i3++;
    if (next === ugly[i5] * 5) i5++;
  }
  return ugly[n - 1];
}
const nthUglyNumber = solve;
class Solution { nthUglyNumber(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, nthUglyNumber };
