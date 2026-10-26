'use strict';

// 1231. Divide Chocolate.
// Binary search the smallest piece value with a greedy feasibility scan; O(n log(sum)) time, O(1) auxiliary space. Inputs are preserved.

function solve(sweetness, k) {
  let low = 1;
  let high = Math.floor(sweetness.reduce((sum, value) => sum + value, 0) / (k + 1));
  while (low < high) {
    const target = Math.floor((low + high + 1) / 2);
    let current = 0, pieces = 0;
    for (const value of sweetness) {
      current += value;
      if (current >= target) { pieces += 1; current = 0; }
    }
    if (pieces >= k + 1) low = target;
    else high = target - 1;
  }
  return low;
}

const maximizeSweetness = solve;
class Solution {
  maximizeSweetness(sweetness, k) { return solve(sweetness, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximizeSweetness };
