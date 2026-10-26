'use strict';

// 2842. Count K-Subsequences of a String With Maximum Beauty. Choose the highest character frequencies and count ties at the cutoff; O(n+26 log 26) time and O(26) space. Inputs are preserved.

function solve(s, k) {
  const modulus = 1000000007n;
  if (k === 0) return 1;
  const counts = Array(26).fill(0);
  for (let index = 0; index < s.length; index += 1) counts[s.charCodeAt(index) - 97] += 1;
  const frequencies = counts.filter(count => count > 0).sort((a, b) => b - a);
  if (k > frequencies.length) return 0;
  const cutoff = frequencies[k - 1];
  let greater = 0;
  let equal = 0;
  let answer = 1n;
  for (const frequency of frequencies) {
    if (frequency > cutoff) { greater += 1; answer = answer * BigInt(frequency) % modulus; }
    else if (frequency === cutoff) equal += 1;
  }
  const needed = k - greater;
  let combinations = 1n;
  for (let selected = 1; selected <= needed; selected += 1) combinations = combinations * BigInt(equal - selected + 1) / BigInt(selected);
  answer = answer * combinations % modulus;
  for (let selected = 0; selected < needed; selected += 1) answer = answer * BigInt(cutoff) % modulus;
  return Number(answer);
}

const countKSubsequencesWithMaxBeauty = solve;
class Solution {
  countKSubsequencesWithMaxBeauty(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countKSubsequencesWithMaxBeauty };
