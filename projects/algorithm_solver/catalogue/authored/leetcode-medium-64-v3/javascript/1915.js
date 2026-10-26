'use strict';

// 1915. Number of Wonderful Substrings: count equal parity masks and masks differing in one of ten bits.
// O(10 * n) time and O(2^10) auxiliary space; inputs are read-only.
function solve(word) {
  const counts = new Float64Array(1024);
  counts[0] = 1;
  let mask = 0;
  let answer = 0;
  for (const char of word) {
    mask ^= 1 << (char.charCodeAt(0) - 97);
    answer += counts[mask];
    for (let bit = 0; bit < 10; bit += 1) answer += counts[mask ^ (1 << bit)];
    counts[mask] += 1;
  }
  return answer;
}

const wonderfulSubstrings = solve;
class Solution {
  wonderfulSubstrings(word) { return solve(word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, wonderfulSubstrings };
