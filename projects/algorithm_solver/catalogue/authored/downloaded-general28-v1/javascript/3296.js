'use strict';

// 3296. Minimum Number of Seconds to Make Mountain Height Zero (Medium).
// Specification: https://leetcode.com/problems/minimum-number-of-seconds-to-make-mountain-height-zero/description/
function solve(mountainHeight, workerTimes) {
  function enough(mid) {
    let total = 0;
    for (const w of workerTimes) {
      total += Math.floor((Math.sqrt(1 + 8 * mid / w) - 1) / 2);
      if (total >= mountainHeight) return true;
    }
    return total >= mountainHeight;
  }
  const wmax = Math.max(...workerTimes);
  let lo = 0; let hi = wmax * mountainHeight * (mountainHeight + 1) / 2;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (enough(mid)) hi = mid; else lo = mid + 1;
  }
  return lo;
}
const minNumberOfSeconds = solve;
class Solution { minNumberOfSeconds(mountainHeight, workerTimes) { return solve(mountainHeight, workerTimes); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minNumberOfSeconds };
