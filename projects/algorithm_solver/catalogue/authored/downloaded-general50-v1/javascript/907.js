'use strict';

// 907. Sum of Subarray Minimums (Medium).
// Specification: https://leetcode.com/problems/sum-of-subarray-minimums/description/
function solve(arr) {
  const MOD = 1000000007;
  const n = arr.length;
  const left = new Array(n); const right = new Array(n);
  let stack = [];
  for (let i = 0; i < n; i++) {
    while (stack.length > 0 && arr[stack[stack.length - 1]] > arr[i]) stack.pop();
    left[i] = stack.length === 0 ? i + 1 : i - stack[stack.length - 1];
    stack.push(i);
  }
  stack = [];
  for (let i = n - 1; i >= 0; i--) {
    while (stack.length > 0 && arr[stack[stack.length - 1]] >= arr[i]) stack.pop();
    right[i] = stack.length === 0 ? n - i : stack[stack.length - 1] - i;
    stack.push(i);
  }
  let total = 0;
  for (let i = 0; i < n; i++) total = (total + arr[i] * left[i] * right[i]) % MOD;
  return total;
}
const sumSubarrayMins = solve;
class Solution { sumSubarrayMins(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumSubarrayMins };
