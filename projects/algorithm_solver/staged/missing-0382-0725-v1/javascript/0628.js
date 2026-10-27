'use strict';

// 628. Maximum Product of Three Numbers.

function solve(nums) {
  const largest = [], smallest = [];
  for (const value of nums) {
    largest.push(value); largest.sort((a, b) => b - a); if (largest.length > 3) largest.pop();
    smallest.push(value); smallest.sort((a, b) => a - b); if (smallest.length > 2) smallest.pop();
  }
  return Math.max(largest[0] * largest[1] * largest[2], largest[0] * smallest[0] * smallest[1]);
}

const maximumProduct = solve;
class Solution {
  maximumProduct(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumProduct };
