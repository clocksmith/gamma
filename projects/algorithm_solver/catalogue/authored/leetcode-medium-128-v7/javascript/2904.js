'use strict';

// 2904. Shortest and Lexicographically Smallest Beautiful String: compare minimal substrings spanning each consecutive group of k one positions.
// O(n * n) worst-case time and O(n) auxiliary space; inputs are read-only.
function solve(s, k) {
  const positions = [];
  for (let index = 0; index < s.length; index += 1) if (s[index] === '1') positions.push(index);
  let best = '';
  for (let index = 0; index + k <= positions.length; index += 1) {
    const left = positions[index];
    const right = positions[index + k - 1] + 1;
    if (best !== '' && right - left > best.length) continue;
    const candidate = s.slice(left, right);
    if (best === '' || candidate.length < best.length || candidate < best) best = candidate;
  }
  return best;
}

const shortestBeautifulSubstring = solve;
class Solution {
  shortestBeautifulSubstring(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestBeautifulSubstring };
