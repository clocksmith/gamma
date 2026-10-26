'use strict';

// 3693. Climbing Stairs II.
// O(n) time and O(1) auxiliary space; landing cost uses zero-based costs[step - 1].
function solve(n, costs) {
  let last = 0;
  let second = Infinity;
  let third = Infinity;
  for (let step = 1; step <= n; step += 1) {
    const best = Math.min(last + 1, second + 4, third + 9) + costs[step - 1];
    third = second;
    second = last;
    last = best;
  }
  return last;
}

const climbStairs = solve;
class Solution {
  climbStairs(n, costs) { return solve(n, costs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, climbStairs };
