'use strict';

// 187. Repeated DNA Sequences (Medium).
// Specification: https://leetcode.com/problems/repeated-dna-sequences/description/
function solve(s) {
  const seen = new Set(); const repeated = new Set();
  for (let i = 0; i + 10 <= s.length; i++) {
    const part = s.slice(i, i + 10);
    if (seen.has(part)) repeated.add(part);
    else seen.add(part);
  }
  return [...repeated].sort();
}
const findRepeatedDnaSequences = solve;
class Solution { findRepeatedDnaSequences(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findRepeatedDnaSequences };
