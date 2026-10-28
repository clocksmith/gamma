'use strict';

// 1114. Number of Ways to Stay in the Same Place After Some Steps (Medium).
// Specification: https://leetcode.com/problems/number-of-ways-to-stay-in-the-same-place-after-some-steps/description/
function solve(steps, arrLen) {
  const modulus = 1000000007;
  const maxPosition = Math.min(steps, arrLen - 1);
  let dp = new Array(maxPosition + 1).fill(0);
  dp[0] = 1;
  for (let step = 0; step < steps; step++) {
    const next = new Array(maxPosition + 1).fill(0);
    for (let position = 0; position <= maxPosition; position++) {
      if (dp[position] === 0) continue;
      next[position] = (next[position] + dp[position]) % modulus;
      if (position > 0) next[position - 1] = (next[position - 1] + dp[position]) % modulus;
      if (position < maxPosition) next[position + 1] = (next[position + 1] + dp[position]) % modulus;
    }
    dp = next;
  }
  return dp[0];
}
const numWays = solve;
class Solution { numWays(steps, arrLen) { return solve(steps, arrLen); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numWays };
