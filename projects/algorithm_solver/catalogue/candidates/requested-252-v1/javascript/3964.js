/**
 * 3964. Minimum Lights to Illuminate a Road
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-lights-to-illuminate-a-road/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3964.Minimum%20Lights%20to%20Illuminate%20a%20Road/README_EN.md
 * Complexity: O(n) time and space.
 * Greedily cover the first uncovered cell using a new lamp as far right as possible. Existing lights are retained; inputs preserved.
 */

function solve(lights) {
  const n = lights.length;
  const difference = new Int32Array(n + 1);
  for (let index = 0; index < n; index++) {
    const radius = lights[index];
    if (radius === 0) continue;
    difference[Math.max(0, index - radius)]++;
    difference[Math.min(n, index + radius + 1)]--;
  }
  let coverage = 0;
  let addedUntil = -1;
  let answer = 0;
  for (let index = 0; index < n; index++) {
    coverage += difference[index];
    if (coverage === 0 && index > addedUntil) {
      answer++;
      addedUntil = Math.min(n - 1, index + 2);
    }
  }
  return answer;
}

function minLights(lights) {
  return solve(lights);
}

class Solution {
  minLights(lights) {
    return solve(lights);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minLights, Solution };
}
