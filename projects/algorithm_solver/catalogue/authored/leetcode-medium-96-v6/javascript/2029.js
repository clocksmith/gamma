'use strict';

// 2029. Stone Game IX: reduce optimal play to residue counts and the parity of zero-residue moves.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(stones) {
  const counts = [0, 0, 0];
  for (const stone of stones) counts[stone % 3] += 1;
  if (counts[0] % 2 === 0) return counts[1] > 0 && counts[2] > 0;
  return Math.abs(counts[1] - counts[2]) > 2;
}

const stoneGameIX = solve;
class Solution {
  stoneGameIX(stones) { return solve(stones); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, stoneGameIX };
