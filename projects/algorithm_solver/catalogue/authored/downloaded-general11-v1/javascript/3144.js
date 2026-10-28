'use strict';

// 3144. Minimum Substring Partition of Equal Character Frequency (Medium).
// Specification: https://leetcode.com/problems/minimum-substring-partition-of-equal-character-frequency/description/
function solve(s) {
  const n = s.length; const dp = new Array(n + 1).fill(Infinity); dp[0] = 0;
  for (let end = 0; end < n; end++) {
    const counts = {};
    for (let start = end; start >= 0; start--) {
      counts[s[start]] = (counts[s[start]] || 0) + 1;
      const vals = Object.values(counts);
      if (Math.min(...vals) === Math.max(...vals)) {
        dp[end + 1] = Math.min(dp[end + 1], dp[start] + 1);
      }
    }
  }
  return dp[n];
}
const minimumSubstringsInPartition = solve;
class Solution { minimumSubstringsInPartition(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumSubstringsInPartition };
