'use strict';

// 3784. Minimum Deletion Cost to Make All Characters Equal.
// O(n) time and O(26) space; retain every occurrence of the letter with maximum total deletion cost.
function solve(s, cost) {
  const totals = new Float64Array(26);
  let total = 0;
  for (let index = 0; index < s.length; index += 1) {
    totals[s.charCodeAt(index) - 97] += cost[index];
    total += cost[index];
  }
  let kept = 0;
  for (const value of totals) kept = Math.max(kept, value);
  return total - kept;
}

const minCost = solve;
class Solution {
  minCost(s, cost) { return solve(s, cost); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
