'use strict';

// 3563. Lexicographically Smallest String After Adjacent Removals.
// Interval dynamic programming recognizes erasable substrings; suffix choices select the lexicographically smallest remainder; O(n^3) time and O(n^2) space. Input is preserved.

function solve(s) {
  const n = s.length, erased = Array.from({ length: n + 1 }, () => new Uint8Array(n + 1));
  for (let index = 0; index <= n; index += 1) erased[index][index] = 1;
  for (let length = 2; length <= n; length += 2) {
    for (let start = 0; start + length <= n; start += 1) {
      const end = start + length;
      for (let partner = start + 1; partner < end; partner += 2) {
        const difference = Math.abs(s.charCodeAt(start) - s.charCodeAt(partner));
        if ((difference === 1 || difference === 25) && erased[start + 1][partner] && erased[partner + 1][end]) { erased[start][end] = 1; break; }
      }
    }
  }
  const best = Array(n + 1).fill('');
  for (let start = n - 1; start >= 0; start -= 1) {
    let candidate = s[start] + best[start + 1];
    for (let end = start + 2; end <= n; end += 2) if (erased[start][end] && best[end] < candidate) candidate = best[end];
    best[start] = candidate;
  }
  return best[0];
}

const lexicographicallySmallestString = solve;
class Solution {
  lexicographicallySmallestString(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lexicographicallySmallestString };
