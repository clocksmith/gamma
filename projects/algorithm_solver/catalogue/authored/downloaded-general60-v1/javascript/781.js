'use strict';

// 781. Rabbits in Forest (Medium).
// Specification: https://leetcode.com/problems/rabbits-in-forest/description/
function solve(answers) {
  const counts = {};
  for (const value of answers) counts[value] = (counts[value] || 0) + 1;
  let total = 0;
  for (const key in counts) {
    const answer = Number(key);
    const count = counts[key];
    const groupSize = answer + 1;
    total += Math.ceil(count / groupSize) * groupSize;
  }
  return total;
}
const numRabbits = solve;
class Solution { numRabbits(answers) { return solve(answers); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numRabbits };
