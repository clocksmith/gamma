'use strict';

// 3789. Minimum Cost to Acquire Required Items.
// O(1) time and O(1) space; a piecewise-linear optimum occurs at one of three demand breakpoints.
function solve(cost1, cost2, costBoth, need1, need2) {
  let answer = cost1 * need1 + cost2 * need2;
  for (const both of [Math.min(need1, need2), Math.max(need1, need2)]) {
    const cost = both * costBoth + Math.max(0, need1 - both) * cost1 + Math.max(0, need2 - both) * cost2;
    answer = Math.min(answer, cost);
  }
  return answer;
}

const minimumCost = solve;
class Solution {
  minimumCost(cost1, cost2, costBoth, need1, need2) { return solve(cost1, cost2, costBoth, need1, need2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumCost };
