'use strict';

// 3303. Find the Occurrence of First Almost Equal Substring.
// Forward and reversed Z matches cover every position except at most one; O(n+m) time and space. Lowercase input strings are preserved.

function solve(s, pattern) {
  function zValues(text) {
    const z = new Int32Array(text.length);
    let left = 0, right = 0;
    for (let index = 1; index < text.length; index += 1) {
      if (index <= right) z[index] = Math.min(right - index + 1, z[index - left]);
      while (index + z[index] < text.length && text[z[index]] === text[index + z[index]]) z[index] += 1;
      if (index + z[index] - 1 > right) { left = index; right = index + z[index] - 1; }
    }
    return z;
  }
  const n = s.length, m = pattern.length;
  if (m > n) return -1;
  const forward = zValues(pattern + '#' + s);
  const backward = zValues(pattern.split('').reverse().join('') + '#' + s.split('').reverse().join(''));
  for (let start = 0; start + m <= n; start += 1) {
    if (forward[m + 1 + start] + backward[m + 1 + n - start - m] >= m - 1) return start;
  }
  return -1;
}

const minStartingIndex = solve;
class Solution {
  minStartingIndex(s, pattern) { return solve(s, pattern); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minStartingIndex };
