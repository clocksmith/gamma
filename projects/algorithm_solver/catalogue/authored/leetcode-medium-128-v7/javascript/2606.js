'use strict';

// 2606. Find the Substring With Maximum Cost: run maximum-subarray accumulation over the declared character costs.
// O(n + m) time and O(1) auxiliary space for the lowercase alphabet; inputs are read-only.
function solve(s, chars, vals) {
  const costs = Array.from({ length: 26 }, (_, index) => index + 1);
  for (let index = 0; index < chars.length; index += 1) costs[chars.charCodeAt(index) - 97] = vals[index];
  let current = 0;
  let best = 0;
  for (const character of s) {
    current = Math.max(0, current + costs[character.charCodeAt(0) - 97]);
    best = Math.max(best, current);
  }
  return best;
}

const maximumCostSubstring = solve;
class Solution {
  maximumCostSubstring(s, chars, vals) { return solve(s, chars, vals); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumCostSubstring };
