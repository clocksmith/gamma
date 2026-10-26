'use strict';

// 1406. Stone Game III: suffix score-difference DP; O(n) time and O(n) space. Inputs are preserved.

function solve(stoneValue) {
  const size = stoneValue.length;
  const difference = Array(size + 1).fill(0);
  for (let index = size - 1; index >= 0; index -= 1) {
    let total = 0;
    let best = -Infinity;
    for (let end = index; end < Math.min(size, index + 3); end += 1) {
      total += stoneValue[end];
      best = Math.max(best, total - difference[end + 1]);
    }
    difference[index] = best;
  }
  return difference[0] > 0 ? 'Alice' : difference[0] < 0 ? 'Bob' : 'Tie';
}

const stoneGameIII = solve;
class Solution {
  stoneGameIII(stoneValue) { return solve(stoneValue); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, stoneGameIII };
