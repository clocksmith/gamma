'use strict';

// 433. Minimum Genetic Mutation.

function solve(startGene, endGene, bank) {
  if (startGene === endGene) return 0;
  const available = new Set(bank);
  if (!available.has(endGene)) return -1;
  const queue = [[startGene, 0]];
  available.delete(startGene);
  for (let head = 0; head < queue.length; head += 1) {
    const [gene, distance] = queue[head];
    for (let i = 0; i < gene.length; i += 1) for (const char of 'ACGT') {
      const candidate = gene.slice(0, i) + char + gene.slice(i + 1);
      if (available.has(candidate)) {
        if (candidate === endGene) return distance + 1;
        available.delete(candidate); queue.push([candidate, distance + 1]);
      }
    }
  }
  return -1;
}

const minMutation = solve;
class Solution {
  minMutation(startGene, endGene, bank) { return solve(startGene, endGene, bank); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMutation };
