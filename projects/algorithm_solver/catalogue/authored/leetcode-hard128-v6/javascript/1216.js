'use strict';

// 1216. Valid Palindrome III.
// Minimum-deletion interval DP with a rolling row; O(n^2) time, O(n) space. Inputs are preserved.

function solve(s, k) {
  const n = s.length;
  const deletions = Array(n).fill(0);
  for (let left = n - 2; left >= 0; left -= 1) {
    let diagonal = 0;
    for (let right = left + 1; right < n; right += 1) {
      const old = deletions[right];
      deletions[right] = s[left] === s[right] ? diagonal : 1 + Math.min(deletions[right], deletions[right - 1]);
      diagonal = old;
    }
  }
  return n === 0 || deletions[n - 1] <= k;
}

const isValidPalindrome = solve;
class Solution {
  isValidPalindrome(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isValidPalindrome };
