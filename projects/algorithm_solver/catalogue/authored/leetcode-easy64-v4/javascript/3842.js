'use strict';

// 3842. Toggle Light Bulbs (Easy).
// Specification: https://leetcode.com/problems/toggle-light-bulbs/description/
// O(n + 100) time, O(100) space; preserve bulbs and return lit labels in ascending order.
function solve(bulbs) {
  const lit = new Array(101).fill(false);
  for (const bulb of bulbs) lit[bulb] = !lit[bulb];
  const result = [];
  for (let bulb = 1; bulb <= 100; bulb++) {
    if (lit[bulb]) result.push(bulb);
  }
  return result;
}

const toggleLightBulbs = solve;
class Solution {
  toggleLightBulbs(bulbs) { return solve(bulbs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, toggleLightBulbs };
