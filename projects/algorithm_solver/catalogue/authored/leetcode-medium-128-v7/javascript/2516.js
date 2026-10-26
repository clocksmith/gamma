'use strict';

// 2516. Take K of Each Character From Left and Right: retain the longest middle window leaving at least k of each character outside.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s, k) {
  const remaining = [0, 0, 0];
  for (const character of s) remaining[character.charCodeAt(0) - 97] += 1;
  if (remaining.some(count => count < k)) return -1;
  let left = 0;
  let best = 0;
  for (let right = 0; right < s.length; right += 1) {
    const code = s.charCodeAt(right) - 97;
    remaining[code] -= 1;
    while (remaining[code] < k) {
      remaining[s.charCodeAt(left) - 97] += 1;
      left += 1;
    }
    best = Math.max(best, right - left + 1);
  }
  return s.length - best;
}

const takeCharacters = solve;
class Solution {
  takeCharacters(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, takeCharacters };
