'use strict';

// 2555. Maximize Win From Two Segments: combine each sliding segment with the best earlier disjoint segment.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(prizePositions, k) {
  const bestPrefix = new Int32Array(prizePositions.length + 1);
  let left = 0;
  let best = 0;
  for (let right = 0; right < prizePositions.length; right += 1) {
    while (prizePositions[right] - prizePositions[left] > k) left += 1;
    const width = right - left + 1;
    best = Math.max(best, width + bestPrefix[left]);
    bestPrefix[right + 1] = Math.max(bestPrefix[right], width);
  }
  return best;
}

const maximizeWin = solve;
class Solution {
  maximizeWin(prizePositions, k) { return solve(prizePositions, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximizeWin };
