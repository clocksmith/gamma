'use strict';

// 2604. Minimum Time to Eat All Grains (Hard).
// Specification: https://leetcode.com/problems/minimum-time-to-eat-all-grains/description/
function solve(hens, grains) {
  const h = hens.slice().sort((a, b) => a - b);
  const g = grains.slice().sort((a, b) => a - b);
  const m = g.length;
  function check(t) {
    let j = 0;
    for (const x of h) {
      if (j === m) return true;
      const y = g[j];
      if (y <= x) {
        const d = x - y;
        if (d > t) return false;
        while (j < m && g[j] <= x) j++;
        while (j < m && Math.min(d, g[j] - x) + g[j] - y <= t) j++;
      } else {
        while (j < m && g[j] - x <= t) j++;
      }
    }
    return j === m;
  }
  let lo = 0;
  let hi = Math.abs(h[0] - g[0]) + g[m - 1] - g[0];
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (check(mid)) hi = mid; else lo = mid + 1;
  }
  return lo;
}
const minimumTime = solve;
class Solution { minimumTime(hens, grains) { return solve(hens, grains); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTime };
