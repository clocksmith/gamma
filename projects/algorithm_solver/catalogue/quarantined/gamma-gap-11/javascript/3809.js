'use strict';

// 3809. Best Reachable Tower.
// O(n) time and O(1) auxiliary space; returns fresh coordinates and preserves inputs.
function solve(towers, center, radius) {
  let best = [-1, -1];
  let quality = -1;
  for (const [x, y, value] of towers) {
    if (Math.abs(x - center[0]) + Math.abs(y - center[1]) > radius) continue;
    if (value > quality || (value === quality && (x < best[0] || (x === best[0] && y < best[1])))) {
      quality = value;
      best = [x, y];
    }
  }
  return best;
}

const bestTower = solve;
class Solution {
  bestTower(towers, center, radius) { return solve(towers, center, radius); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, bestTower };
