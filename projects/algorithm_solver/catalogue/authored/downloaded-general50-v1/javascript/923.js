'use strict';

// 923. 3Sum With Multiplicity (Medium).
// Specification: https://leetcode.com/problems/3sum-with-multiplicity/description/
function solve(arr, target) {
  const MOD = 1000000007;
  const count = new Array(101).fill(0);
  for (const v of arr) count[v]++;
  let total = 0;
  for (let i = 0; i <= 100; i++) {
    for (let j = i; j <= 100; j++) {
      const k = target - i - j;
      if (k < j || k > 100) continue;
      if (count[i] === 0 || count[j] === 0 || count[k] === 0) continue;
      if (i === j && j === k) total = (total + count[i] * (count[i] - 1) * (count[i] - 2) / 6) % MOD;
      else if (i === j) total = (total + count[i] * (count[i] - 1) / 2 * count[k]) % MOD;
      else if (j === k) total = (total + count[i] * count[j] * (count[j] - 1) / 2) % MOD;
      else total = (total + count[i] * count[j] * count[k]) % MOD;
    }
  }
  return total;
}
const threeSumMulti = solve;
class Solution { threeSumMulti(arr, target) { return solve(arr, target); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, threeSumMulti };
