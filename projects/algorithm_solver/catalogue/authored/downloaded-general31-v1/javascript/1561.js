'use strict';

// 1561. Maximum Number of Coins You Can Get (Medium).
// Specification: https://leetcode.com/problems/maximum-number-of-coins-you-can-get/description/
function solve(piles) {
  const sorted = piles.slice().sort((a, b) => b - a);
  let total = 0;
  for (let i = 1; i < sorted.length; i += 3) {
    if (i >= sorted.length - (sorted.length / 3) * 2) break;
    total += sorted[i];
  }
  const groups = Math.floor(sorted.length / 3);
  total = 0;
  for (let group = 0; group < groups; group++) total += sorted[group * 2 + 1];
  return total;
}
const maxCoins = solve;
class Solution { maxCoins(piles) { return solve(piles); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxCoins };
