'use strict';

// 2400. Number of Ways to Reach a Position After Exactly k Steps (Medium).
// Specification: https://leetcode.com/problems/number-of-ways-to-reach-a-position-after-exactly-k-steps/description/
function solve(startPos, endPos, k) {
  const MOD = 1000000007;
  let cur = new Map([[Math.abs(startPos - endPos), 1]]);
  for (let step = 0; step < k; step++) {
    const nxt = new Map();
    for (const [d, ways] of cur) {
      const add = (nd) => nxt.set(nd, ((nxt.get(nd) || 0) + ways) % MOD);
      add(d + 1);
      add(Math.abs(d - 1));
    }
    cur = nxt;
  }
  return cur.get(0) || 0;
}
const numberOfWays = solve;
class Solution { numberOfWays(startPos, endPos, k) { return solve(startPos, endPos, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfWays };
