/**
 * 4050. Minimum Days to Score Exactly N Points
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-days-to-score-exactly-n-points/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4050.Minimum%20Days%20to%20Score%20Exactly%20N%20Points/README_EN.md
 * Complexity: O(n sqrt(n)) time, O(n) space.
 * Unbounded triangular-score knapsack. Charge one skip after every streak, then remove the final skip. No global precomputation or dependencies.
 */

function solve(n) {
  const best=new Int32Array(n+1);best.fill(2*n+1);best[0]=0;
  for(let length=1;length*(length+1)/2<=n;length++) {
    const score=length*(length+1)/2,cost=length+1;
    for(let total=score;total<=n;total++)best[total]=Math.min(best[total],best[total-score]+cost);
  }
  return best[n]-1;
}

function minDays(n) {
  return solve(n);
}

class Solution {
  minDays(n) {
    return solve(n);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minDays, Solution };
}
