'use strict';

// 1981. Minimize the Difference Between Target and Chosen Elements: keep all attainable sums below target and only the smallest overflowing sum.
// O(rows * columns * (target + 1)) expected time and O(target + columns) auxiliary space; inputs are read-only.
function solve(mat, target) {
  let reachable = new Set([0]);
  for (const row of mat) {
    const choices = new Set(row);
    const next = new Set();
    let smallestOverflow = Infinity;
    for (const total of reachable) {
      for (const value of choices) {
        const candidate = total + value;
        if (candidate <= target) next.add(candidate);
        else smallestOverflow = Math.min(smallestOverflow, candidate);
      }
    }
    // All future additions are positive, so larger overflows are dominated.
    if (smallestOverflow !== Infinity) next.add(smallestOverflow);
    reachable = next;
  }
  let result = Infinity;
  for (const total of reachable) result = Math.min(result, Math.abs(total - target));
  return result;
}

const minimizeTheDifference = solve;
class Solution {
  minimizeTheDifference(mat, target) { return solve(mat, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimizeTheDifference };
