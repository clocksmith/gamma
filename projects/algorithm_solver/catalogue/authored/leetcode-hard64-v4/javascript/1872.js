'use strict';

// 1872. Stone Game VIII. Backward minimax over prefix sums; O(n) time and O(n) space. Inputs are preserved.

function solve(stones) {
  const prefix = [];
  let total = 0;
  for (const value of stones) {
    total += value;
    prefix.push(total);
  }
  let best = prefix[prefix.length - 1];
  for (let index = stones.length - 2; index >= 1; index -= 1) {
    best = Math.max(best, prefix[index] - best);
  }
  return best;
}

const stoneGameVIII = solve;
class Solution {
  stoneGameVIII(stones) { return solve(stones); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, stoneGameVIII };
