'use strict';

// 477. Total Hamming Distance.

function solve(nums) {
  let answer = 0;
  for (let bit = 0; bit < 31; bit += 1) {
    let ones = 0;
    for (const value of nums) ones += (value >>> bit) & 1;
    answer += ones * (nums.length - ones);
  }
  return answer;
}

const totalHammingDistance = solve;
class Solution {
  totalHammingDistance(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, totalHammingDistance };
