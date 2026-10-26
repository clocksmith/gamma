'use strict';

// 1646. Get Maximum in Generated Array (Easy).
// Specification: https://leetcode.com/problems/get-maximum-in-generated-array/description/
// O(n) time and space; generated values are local to this call.
function solve(n) {
  if (n <= 1) return n;
  const values = new Array(n + 1).fill(0);
  values[1] = 1;
  let maximum = 1;
  for (let index = 2; index <= n; index++) {
    const half = Math.floor(index / 2);
    values[index] = values[half];
    if (index % 2 === 1) values[index] += values[half + 1];
    maximum = Math.max(maximum, values[index]);
  }
  return maximum;
}

const getMaximumGenerated = solve;
class Solution {
  getMaximumGenerated(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getMaximumGenerated };
