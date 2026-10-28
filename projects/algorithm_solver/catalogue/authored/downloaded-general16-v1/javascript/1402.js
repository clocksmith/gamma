'use strict';

// 1402. Reducing Dishes (Hard).
// Specification: https://leetcode.com/problems/reducing-dishes/description/
function solve(satisfaction) {
  const sorted = [...satisfaction].sort((a, b) => b - a);
  let running = 0; let total = 0;
  for (const value of sorted) {
    running += value;
    if (running > 0) total += running; else break;
  }
  return total;
}
const maxSatisfaction = solve;
class Solution { maxSatisfaction(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSatisfaction };
