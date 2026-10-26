'use strict';

// 3800. Minimum Cost to Make Two Binary Strings Equal.
// O(n) time and O(1) space; resolve opposite mismatches before equal-direction pairs.
function solve(s, t, flipCost, swapCost, crossCost) {
  let forward = 0;
  let backward = 0;
  for (let index = 0; index < s.length; index += 1) {
    if (s[index] === t[index]) continue;
    if (s[index] === '0') forward += 1;
    else backward += 1;
  }
  const opposite = Math.min(forward, backward);
  const remaining = Math.abs(forward - backward);
  return opposite * Math.min(swapCost, 2 * flipCost)
    + Math.floor(remaining / 2) * Math.min(crossCost + swapCost, 2 * flipCost)
    + remaining % 2 * flipCost;
}

const minimumCost = solve;
class Solution {
  minimumCost(s, t, flipCost, swapCost, crossCost) { return solve(s, t, flipCost, swapCost, crossCost); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumCost };
