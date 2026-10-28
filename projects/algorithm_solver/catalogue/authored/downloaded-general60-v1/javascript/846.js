'use strict';

// 846. Hand of Straights (Medium).
// Specification: https://leetcode.com/problems/hand-of-straights/description/
function solve(hand, groupSize) {
  if (hand.length % groupSize !== 0) return false;
  const counts = {};
  for (const value of hand) counts[value] = (counts[value] || 0) + 1;
  const keys = Object.keys(counts).map(Number).sort((a, b) => a - b);
  for (const start of keys) {
    const need = counts[start];
    if (need === 0) continue;
    for (let value = start; value < start + groupSize; value++) {
      if ((counts[value] || 0) < need) return false;
      counts[value] -= need;
    }
  }
  return true;
}
const isNStraightHand = solve;
class Solution { isNStraightHand(hand, groupSize) { return solve(hand, groupSize); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isNStraightHand };
