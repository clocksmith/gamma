'use strict';

// 3335. Total Characters in String After Transformations I (Medium).
// Specification: https://leetcode.com/problems/total-characters-in-string-after-transformations-i/description/
function solve(s, t) {
  const MOD = 1000000007;
  let counts = Array(26).fill(0);
  for (const ch of s) counts[ch.charCodeAt(0) - 97]++;
  for (let step = 0; step < t; step++) {
    const next = Array(26).fill(0);
    const z = counts[25];
    next[0] = (next[0] + z) % MOD;
    next[1] = (next[1] + z) % MOD;
    for (let i = 0; i < 25; i++) next[i + 1] = (next[i + 1] + counts[i]) % MOD;
    counts = next;
  }
  return counts.reduce((a, b) => (a + b) % MOD, 0);
}
const lengthAfterTransformations = solve;
class Solution { lengthAfterTransformations(s, t) { return solve(s, t); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, lengthAfterTransformations };
