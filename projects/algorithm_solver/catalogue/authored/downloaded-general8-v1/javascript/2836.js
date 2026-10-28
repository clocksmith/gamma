'use strict';

// 2836. Maximize Value of Function in a Ball Passing Game (Hard).
// Specification: https://leetcode.com/problems/maximize-value-of-function-in-a-ball-passing-game/description/
function solve(receiver, k) {
  const n = receiver.length;
  const m = k.toString(2).length;
  const jump = Array.from({ length: n }, () => new Array(m).fill(0));
  const summ = Array.from({ length: n }, () => new Array(m).fill(0));
  for (let i = 0; i < n; i++) { jump[i][0] = receiver[i]; summ[i][0] = receiver[i]; }
  for (let j = 1; j < m; j++) {
    for (let i = 0; i < n; i++) {
      const mid = jump[i][j - 1];
      jump[i][j] = jump[mid][j - 1];
      summ[i][j] = summ[i][j - 1] + summ[mid][j - 1];
    }
  }
  let ans = 0;
  for (let i = 0; i < n; i++) {
    let total = i; let pos = i;
    for (let j = 0; j < m; j++) {
      if ((k >> j) & 1) { total += summ[pos][j]; pos = jump[pos][j]; }
    }
    ans = Math.max(ans, total);
  }
  return ans;
}
const getMaxFunctionValue = solve;
class Solution {
  getMaxFunctionValue(...args) { return solve(...args); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getMaxFunctionValue };
