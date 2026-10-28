'use strict';

// 881. Boats to Save People (Medium).
// Specification: https://leetcode.com/problems/boats-to-save-people/description/
function solve(people, limit) {
  const sorted = people.slice().sort((a, b) => a - b);
  let left = 0; let right = sorted.length - 1; let boats = 0;
  while (left <= right) {
    if (sorted[left] + sorted[right] <= limit) left++;
    right--; boats++;
  }
  return boats;
}
const numRescueBoats = solve;
class Solution { numRescueBoats(people, limit) { return solve(people, limit); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numRescueBoats };
