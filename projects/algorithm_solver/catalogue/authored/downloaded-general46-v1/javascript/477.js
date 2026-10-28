'use strict';

// 477. Total Hamming Distance (Medium).
// Specification: https://leetcode.com/problems/total-hamming-distance/description/
function solve(nums) {
  let total = 0;
  for (let bit = 0; bit < 32; bit++) {
    let ones = 0;
    for (const value of nums) { if ((value >> bit) & 1) ones++; }
    total += ones * (nums.length - ones);
  }
  return total;
}
const totalHammingDistance = solve;
class Solution { totalHammingDistance(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, totalHammingDistance };
