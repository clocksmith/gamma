'use strict';

// 1521. Find a Value of a Mysterious Function Closest to Target.
// O(n*b) time, O(b) space. Declared inputs are below 2^20, so bitwise AND is exact.
function solve(arr, target) {
  let previous = new Set();
  let answer = Math.abs(arr[0] - target);
  for (const value of arr) {
    const current = new Set([value]);
    for (const suffix of previous) current.add(suffix & value);
    for (const result of current) answer = Math.min(answer, Math.abs(result - target));
    if (answer === 0) return 0;
    previous = current;
  }
  return answer;
}

const closestToTarget = solve;
class Solution {
  closestToTarget(arr, target) { return solve(arr, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, closestToTarget };
