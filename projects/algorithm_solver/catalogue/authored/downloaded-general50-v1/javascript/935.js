'use strict';

// 935. Knight Dialer (Medium).
// Specification: https://leetcode.com/problems/knight-dialer/description/
const MOVES = { 0: [4, 6], 1: [6, 8], 2: [7, 9], 3: [4, 8], 4: [3, 9, 0], 5: [], 6: [1, 7, 0], 7: [2, 6], 8: [1, 3], 9: [2, 4] };
function solve(n) {
  const MOD = 1000000007;
  let dp = new Array(10).fill(1);
  for (let step = 1; step < n; step++) {
    const next = new Array(10).fill(0);
    for (let digit = 0; digit < 10; digit++) {
      for (const dest of MOVES[digit]) next[dest] = (next[dest] + dp[digit]) % MOD;
    }
    dp = next;
  }
  return dp.reduce((s, v) => (s + v) % MOD, 0);
}
const knightDialer = solve;
class Solution { knightDialer(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, knightDialer };
