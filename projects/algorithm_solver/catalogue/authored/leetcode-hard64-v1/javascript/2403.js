'use strict';

// 2403. Minimum Time to Kill All Monsters: subset dynamic programming with kill-count energy gain.
// O(n * 2^n) time and O(2^n) auxiliary space. Inputs are preserved.
function solve(power) {
  const length = power.length;
  const size = 1 << length;
  const count = new Uint8Array(size);
  for (let mask = 1; mask < size; mask += 1) count[mask] = count[mask >> 1] + (mask & 1);
  const best = new Float64Array(size).fill(Infinity);
  best[0] = 0;
  for (let mask = 0; mask < size; mask += 1) {
    const gain = count[mask] + 1;
    for (let monster = 0; monster < length; monster += 1) {
      const bit = 1 << monster;
      if (mask & bit) continue;
      const days = Math.floor((power[monster] + gain - 1) / gain);
      const following = mask | bit;
      best[following] = Math.min(best[following], best[mask] + days);
    }
  }
  return best[size - 1];
}

const minimumTime = solve;
class Solution {
  minimumTime(power) { return solve(power); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTime };
