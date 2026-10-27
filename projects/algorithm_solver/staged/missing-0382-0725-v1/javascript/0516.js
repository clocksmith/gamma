'use strict';

// 516. Longest Palindromic Subsequence. Rolling interval dynamic programming; O(n^2) time and O(n) space.

function solve(s) {
  const n = s.length;
  if (n === 0) return 0;
  const dp = Array(n).fill(0);
  for (let left = n - 1; left >= 0; left -= 1) {
    let diagonal = 0;
    dp[left] = 1;
    for (let right = left + 1; right < n; right += 1) {
      const previous = dp[right];
      dp[right] = s[left] === s[right] ? diagonal + 2 : Math.max(dp[right], dp[right - 1]);
      diagonal = previous;
    }
  }
  return dp[n - 1];
}

const longestPalindromeSubseq = solve;
class Solution {
  longestPalindromeSubseq(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestPalindromeSubseq };
