'use strict';

// 2028. Find Missing Observations: distribute the required missing sum as evenly as possible.
// O(m + n) time and O(n) result space; inputs are read-only.
function solve(rolls, mean, n) {
  let observed = 0;
  for (const roll of rolls) observed += roll;
  const missing = mean * (rolls.length + n) - observed;
  if (missing < n || missing > 6 * n) return [];
  const value = Math.floor(missing / n);
  const extra = missing % n;
  return Array.from({ length: n }, (_, index) => value + (index < extra ? 1 : 0));
}

const missingRolls = solve;
class Solution {
  missingRolls(rolls, mean, n) { return solve(rolls, mean, n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, missingRolls };
