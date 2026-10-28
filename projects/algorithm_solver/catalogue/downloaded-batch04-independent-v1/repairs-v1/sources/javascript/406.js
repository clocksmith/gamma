'use strict';

// 406. Queue Reconstruction by Height (Medium).
// Specification: https://leetcode.com/problems/queue-reconstruction-by-height/description/
function solve(people) {
  const sorted = people.slice().sort((a, b) => b[0] - a[0] || a[1] - b[1]);
  const result = [];
  for (const person of sorted) result.splice(person[1], 0, person.slice());
  return result;
}
const reconstructQueue = solve;
class Solution { reconstructQueue(people) { return solve(people); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reconstructQueue };
