/**
 * 3951. Minimum Energy to Maintain Brightness
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-energy-to-maintain-brightness/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3951.Minimum%20Energy%20to%20Maintain%20Brightness/README_EN.md
 * Complexity: O(q log q) time, O(q) space.
 * Inclusive integer times; overlapping requirements count once. Brightness <= n guarantees ceil(brightness/3) bulbs suffice. Maximum energy below 3.34e14 is exactly representable. Inputs preserved.
 */

function solve(n, brightness, intervals) {
  const ordered = intervals.map(pair => pair.slice()).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  let [left, right] = ordered[0];
  let duration = 0;
  for (let index = 1; index < ordered.length; index++) {
    const [start, end] = ordered[index];
    if (start > right + 1) {
      duration += right - left + 1;
      left = start;
      right = end;
    } else right = Math.max(right, end);
  }
  duration += right - left + 1;
  return duration * Math.ceil(brightness / 3);
}

function minEnergy(n, brightness, intervals) {
  return solve(n, brightness, intervals);
}

class Solution {
  minEnergy(n, brightness, intervals) {
    return solve(n, brightness, intervals);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minEnergy, Solution };
}
