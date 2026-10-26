'use strict';

// 2767. Partition String Into Minimum Beautiful Substrings: partition by binary values that are powers of five and reject leading zeros.
// O(n * n) time and O(n) auxiliary space on the stated binary-length domain; inputs are read-only.
function solve(s) {
  const powers = new Set();
  for (let value = 1; value < 2 ** s.length; value *= 5) powers.add(value);
  const best = new Array(s.length + 1).fill(s.length + 1);
  best[0] = 0;
  for (let start = 0; start < s.length; start += 1) {
    if (s[start] === '0' || best[start] > s.length) continue;
    let value = 0;
    for (let end = start; end < s.length; end += 1) {
      value = 2 * value + Number(s[end]);
      if (powers.has(value)) best[end + 1] = Math.min(best[end + 1], best[start] + 1);
    }
  }
  return best[s.length] <= s.length ? best[s.length] : -1;
}

const minimumBeautifulSubstrings = solve;
class Solution {
  minimumBeautifulSubstrings(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumBeautifulSubstrings };
