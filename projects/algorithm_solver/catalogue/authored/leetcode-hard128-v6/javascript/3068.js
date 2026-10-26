'use strict';

// 3068. Find the Maximum Sum of Node Values.
// On a connected tree any even set of nodes can be toggled; two parity DP states suffice. O(n) time, O(1) space. Inputs are preserved.

function solve(nums, k, edges) {
  let even = 0, odd = -Infinity;
  for (const value of nums) {
    const toggled = value ^ k;
    [even, odd] = [Math.max(even + value, odd + toggled), Math.max(odd + value, even + toggled)];
  }
  return even;
}

const maximumValueSum = solve;
class Solution {
  maximumValueSum(nums, k, edges) { return solve(nums, k, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumValueSum };
