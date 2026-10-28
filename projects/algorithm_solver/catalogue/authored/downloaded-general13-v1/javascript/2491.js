'use strict';

// 2491. Divide Players Into Teams of Equal Skill (Medium).
// Specification: https://leetcode.com/problems/divide-players-into-teams-of-equal-skill/description/
function solve(skill) {
  const sorted = [...skill].sort((a, b) => a - b);
  if (sorted.length % 2 === 1) return -1;
  const target = sorted[0] + sorted[sorted.length - 1];
  let total = 0;
  for (let i = 0; i < sorted.length / 2; i++) {
    if (sorted[i] + sorted[sorted.length - 1 - i] !== target) return -1;
    total += sorted[i] * sorted[sorted.length - 1 - i];
  }
  return total;
}
const dividePlayers = solve;
class Solution { dividePlayers(skill) { return solve(skill); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, dividePlayers };
