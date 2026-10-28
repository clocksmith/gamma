'use strict';

// 2222. Number of Ways to Select Buildings (Medium).
// Specification: https://leetcode.com/problems/number-of-ways-to-select-buildings/description/
function solve(s) {
  const total = [0, 0];
  for (const ch of s) total[ch === '1' ? 1 : 0]++;
  const left = [0, 0];
  const right = total.slice();
  let ans = 0;
  for (const ch of s) {
    const x = ch === '1' ? 1 : 0;
    right[x]--;
    ans += left[1 - x] * right[1 - x];
    left[x]++;
  }
  return ans;
}
const numberOfWays = solve;
class Solution { numberOfWays(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfWays };
