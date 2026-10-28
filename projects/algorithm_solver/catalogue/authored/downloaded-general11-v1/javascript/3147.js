'use strict';

// 3147. Taking Maximum Energy From the Mystic Dungeon (Medium).
// Specification: https://leetcode.com/problems/taking-maximum-energy-from-the-mystic-dungeon/description/
function solve(energy, k) {
  const n = energy.length; const dp = energy.slice(); let best = -Infinity;
  for (let i = n - 1; i >= 0; i--) {
    if (i + k < n) dp[i] += dp[i + k];
    if (dp[i] > best) best = dp[i];
  }
  return best;
}
const maximumEnergy = solve;
class Solution { maximumEnergy(energy, k) { return solve(energy, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumEnergy };
