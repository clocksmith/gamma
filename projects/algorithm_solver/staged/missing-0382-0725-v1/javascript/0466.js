'use strict';

// 466. Count The Repetitions. Skip repeated block-boundary automaton states.

function solve(s1, n1, s2, n2) {
  if (n1 === 0) return 0;
  const alphabet = new Set(s1);
  for (const char of s2) if (!alphabet.has(char)) return 0;
  const seen = new Map([[0, [0, 0]]]);
  let block = 0, index = 0, matches = 0;
  while (block < n1) {
    for (const char of s1) {
      if (char === s2[index]) {
        index += 1;
        if (index === s2.length) { index = 0; matches += 1; }
      }
    }
    block += 1;
    if (seen.has(index)) {
      const [previousBlock, previousMatches] = seen.get(index), cycleLength = block - previousBlock;
      const cycles = Math.floor((n1 - block) / cycleLength);
      if (cycles > 0) { block += cycles * cycleLength; matches += cycles * (matches - previousMatches); }
    } else seen.set(index, [block, matches]);
  }
  return Math.floor(matches / n2);
}

const getMaxRepetitions = solve;
class Solution {
  getMaxRepetitions(s1, n1, s2, n2) { return solve(s1, n1, s2, n2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getMaxRepetitions };
