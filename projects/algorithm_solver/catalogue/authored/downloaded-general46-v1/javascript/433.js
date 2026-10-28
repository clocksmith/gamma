'use strict';

// 433. Minimum Genetic Mutation (Medium).
// Specification: https://leetcode.com/problems/minimum-genetic-mutation/description/
function solve(startGene, endGene, bank) {
  const bankSet = new Set(bank);
  if (!bankSet.has(endGene)) return -1;
  const letters = ['A', 'C', 'G', 'T'];
  let queue = [startGene];
  const visited = new Set([startGene]);
  let steps = 0;
  while (queue.length > 0) {
    const nextQueue = [];
    for (const gene of queue) {
      if (gene === endGene) return steps;
      for (let i = 0; i < gene.length; i++) {
        for (const letter of letters) {
          const candidate = gene.slice(0, i) + letter + gene.slice(i + 1);
          if (bankSet.has(candidate) && !visited.has(candidate)) { visited.add(candidate); nextQueue.push(candidate); }
        }
      }
    }
    queue = nextQueue;
    steps++;
  }
  return -1;
}
const minMutation = solve;
class Solution { minMutation(startGene, endGene, bank) { return solve(startGene, endGene, bank); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMutation };
