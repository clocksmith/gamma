'use strict';

// 2240. Number of Ways to Buy Pens and Pencils: enumerate the more expensive item and count affordable quantities of the other.
// O(total / max(cost1, cost2) + 1) time and O(1) auxiliary space; inputs are read-only.
function solve(total, cost1, cost2) {
  const expensive = Math.max(cost1, cost2);
  const cheap = Math.min(cost1, cost2);
  let answer = 0;
  for (let spent = 0; spent <= total; spent += expensive) {
    answer += Math.floor((total - spent) / cheap) + 1;
  }
  return answer;
}

const waysToBuyPensPencils = solve;
class Solution {
  waysToBuyPensPencils(total, cost1, cost2) { return solve(total, cost1, cost2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, waysToBuyPensPencils };
