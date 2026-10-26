'use strict';

// 2162. Minimum Cost to Set Cooking Time: compare both legal minute-second encodings after omitting unnecessary leading zeros.
// O(1) time and O(1) auxiliary space on the four-digit keypad domain; inputs are read-only.
function solve(startAt, moveCost, pushCost, targetSeconds) {
  const minutes = Math.floor(targetSeconds / 60);
  const seconds = targetSeconds % 60;
  let best = Infinity;
  for (const [minute, second] of [[minutes, seconds], [minutes - 1, seconds + 60]]) {
    if (minute < 0 || minute > 99 || second < 0 || second > 99) continue;
    const digits = String(minute * 100 + second);
    let position = startAt;
    let cost = 0;
    for (const character of digits) {
      const digit = character.charCodeAt(0) - 48;
      if (digit !== position) cost += moveCost;
      cost += pushCost;
      position = digit;
    }
    best = Math.min(best, cost);
  }
  return best;
}

const minCostSetTime = solve;
class Solution {
  minCostSetTime(startAt, moveCost, pushCost, targetSeconds) { return solve(startAt, moveCost, pushCost, targetSeconds); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCostSetTime };
