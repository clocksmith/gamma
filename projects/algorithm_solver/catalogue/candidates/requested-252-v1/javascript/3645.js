'use strict';

// 3645. Maximum Total from Optimal Activation Order.
// Specification: https://leetcode.com/problems/maximum-total-from-optimal-activation-order/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(n log n) time, O(n) space; for each limit L, at most L values can activate before that group disappears.
// Inputs are not modified.

function solve(value, limit) {
  const groups = new Map();
  for (let index = 0; index < value.length; index++) {
    if (!groups.has(limit[index])) groups.set(limit[index], []);
    groups.get(limit[index]).push(value[index]);
  }
  let answer = 0;
  for (const [capacity, scores] of groups) {
    scores.sort((a, b) => b - a);
    for (let index = 0; index < Math.min(capacity, scores.length); index++) answer += scores[index];
  }
  return answer;
}

const maxTotal = solve;
class Solution {
  maxTotal(value, limit) { return solve(value, limit); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxTotal };
