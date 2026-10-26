'use strict';

// 2673. Make Costs of Paths Equal in a Binary Tree: balance child path totals bottom-up in a private copy of the complete tree.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(n, cost) {
  const totals = cost.slice();
  let increments = 0;
  for (let node = Math.floor(n / 2) - 1; node >= 0; node -= 1) {
    const left = 2 * node + 1;
    const right = left + 1;
    increments += Math.abs(totals[left] - totals[right]);
    totals[node] += Math.max(totals[left], totals[right]);
  }
  return increments;
}

const minIncrements = solve;
class Solution {
  minIncrements(n, cost) { return solve(n, cost); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minIncrements };
