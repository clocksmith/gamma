'use strict';

// 2335. Minimum Amount of Time to Fill Cups (Easy).
// Specification: https://leetcode.com/problems/minimum-amount-of-time-to-fill-cups/description/
// O(1) time and space for three amounts; maximum demand and half the total are tight bounds.
function solve(amount) {
  const total = amount[0] + amount[1] + amount[2];
  const largest = Math.max(amount[0], amount[1], amount[2]);
  return Math.max(largest, Math.ceil(total / 2));
}

const fillCups = solve;
class Solution {
  fillCups(amount) { return solve(amount); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, fillCups };
