'use strict';

// 956. Tallest Billboard: difference dynamic programming retaining the greatest shorter support.
// O(n * S) time and O(S) space, S = sum of rods. Inputs are preserved.
function solve(rods) {
  let states = new Map([[0, 0]]);
  for (const rod of rods) {
    const following = new Map(states);
    for (const [difference, shorter] of states) {
      const largerDifference = difference + rod;
      following.set(largerDifference, Math.max(following.get(largerDifference) || 0, shorter));
      const balancedDifference = Math.abs(difference - rod);
      const balancedHeight = shorter + Math.min(difference, rod);
      following.set(balancedDifference, Math.max(following.get(balancedDifference) || 0, balancedHeight));
    }
    states = following;
  }
  return states.get(0);
}

const tallestBillboard = solve;
class Solution {
  tallestBillboard(rods) { return solve(rods); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, tallestBillboard };
