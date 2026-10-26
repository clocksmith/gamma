'use strict';

// 2983. Palindrome Rearrangement Queries.
// Mirror both halves, subtract fixed-position demands, and compare remaining counts; O(26*(n+q)) time and space. Inputs are preserved.

function solve(s, queries) {
  const half = s.length / 2, left = s.slice(0, half), right = s.slice(half).split('').reverse().join('');
  const prefixLeft = [new Int32Array(26)], prefixRight = [new Int32Array(26)], mismatch = [0];
  for (let i = 0; i < half; i += 1) {
    const a = prefixLeft[i].slice(), b = prefixRight[i].slice();
    a[left.charCodeAt(i) - 97] += 1; b[right.charCodeAt(i) - 97] += 1;
    prefixLeft.push(a); prefixRight.push(b); mismatch.push(mismatch[i] + Number(left[i] !== right[i]));
  }
  function mismatches(a, b) { return a > b ? 0 : mismatch[b + 1] - mismatch[a]; }
  return queries.map(([a, b, originalC, originalD]) => {
    const c = s.length - 1 - originalD, d = s.length - 1 - originalC;
    const start = Math.max(a, c), end = Math.min(b, d);
    if (mismatch[half] - mismatches(a, b) - mismatches(c, d) + mismatches(start, end) !== 0) return false;
    for (let letter = 0; letter < 26; letter += 1) {
      const overlapLeft = start <= end ? prefixLeft[end + 1][letter] - prefixLeft[start][letter] : 0;
      const overlapRight = start <= end ? prefixRight[end + 1][letter] - prefixRight[start][letter] : 0;
      const availableLeft = prefixLeft[b + 1][letter] - prefixLeft[a][letter] - prefixRight[b + 1][letter] + prefixRight[a][letter] + overlapRight;
      const availableRight = prefixRight[d + 1][letter] - prefixRight[c][letter] - prefixLeft[d + 1][letter] + prefixLeft[c][letter] + overlapLeft;
      if (availableLeft < 0 || availableRight < 0 || availableLeft !== availableRight) return false;
    }
    return true;
  });
}

const canMakePalindromeQueries = solve;
class Solution {
  canMakePalindromeQueries(s, queries) { return solve(s, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canMakePalindromeQueries };
