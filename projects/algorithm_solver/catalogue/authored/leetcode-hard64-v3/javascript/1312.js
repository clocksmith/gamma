'use strict';

// 1312. Minimum Insertion Steps to Make a String Palindrome: rolling interval dynamic programming; O(n^2) time and O(n) space.

function solve(s) {
  const best = Array(s.length).fill(0);
  for (let left = s.length - 2; left >= 0; left -= 1) {
    let diagonal = 0;
    for (let right = left + 1; right < s.length; right += 1) {
      const previous = best[right];
      best[right] = s[left] === s[right] ? diagonal : 1 + Math.min(best[right], best[right - 1]);
      diagonal = previous;
    }
  }
  return s.length === 0 ? 0 : best[s.length - 1];
}

const minInsertions = solve;
class Solution {
  minInsertions(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minInsertions };
