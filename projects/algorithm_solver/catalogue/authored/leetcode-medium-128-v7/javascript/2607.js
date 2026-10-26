'use strict';

// 2607. Make K-Subarray Sums Equal: equalize each modular index cycle to its median.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(arr, k) {
  let left = arr.length;
  let right = k;
  while (right !== 0) [left, right] = [right, left % right];
  const groups = left;
  let operations = 0;
  for (let start = 0; start < groups; start += 1) {
    const values = [];
    for (let index = start; index < arr.length; index += groups) values.push(arr[index]);
    values.sort((a, b) => a - b);
    const median = values[Math.floor(values.length / 2)];
    for (const value of values) operations += Math.abs(value - median);
  }
  return operations;
}

const makeSubKSumEqual = solve;
class Solution {
  makeSubKSumEqual(arr, k) { return solve(arr, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, makeSubKSumEqual };
