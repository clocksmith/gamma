'use strict';

// 2188. Minimum Time to Finish the Race. Bounded same-tire stints followed by partition DP; O((T+N)*L) time and O(N) space. Inputs are preserved.

function solve(tires, changeTime, numLaps) {
  const stint = Array(numLaps + 1).fill(Infinity);
  let longest = 0;
  for (const [first, ratio] of tires) {
    let lap = first;
    let total = 0;
    for (let length = 1; length <= numLaps; length += 1) {
      total += lap;
      stint[length] = Math.min(stint[length], total);
      longest = Math.max(longest, length);
      if (lap * ratio >= changeTime + first) break;
      lap *= ratio;
    }
  }
  const best = Array(numLaps + 1).fill(Infinity);
  best[0] = -changeTime;
  for (let laps = 1; laps <= numLaps; laps += 1) {
    for (let length = 1; length <= Math.min(laps, longest); length += 1) {
      best[laps] = Math.min(best[laps], best[laps - length] + changeTime + stint[length]);
    }
  }
  return best[numLaps];
}

const minimumFinishTime = solve;
class Solution {
  minimumFinishTime(tires, changeTime, numLaps) { return solve(tires, changeTime, numLaps); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumFinishTime };
