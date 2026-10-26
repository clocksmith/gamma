'use strict';

// 2835. Minimum Operations to Form Subsequence With Target Sum. Fulfill low target bits by splitting the nearest available larger power; O(n+31^2) time and O(31) space. Inputs are preserved.

function solve(nums, target) {
  let sum = 0;
  for (const value of nums) sum += value;
  if (sum < target) return -1;
  const counts = Array(33).fill(0);
  for (const value of nums) counts[Math.log2(value)] += 1;
  let answer = 0;
  for (let bit = 0; bit < 31; bit += 1) {
    if (Math.floor(target / 2 ** bit) % 2 === 1) {
      let higher = bit;
      while (counts[higher] === 0) higher += 1;
      while (higher > bit) {
        counts[higher] -= 1;
        counts[higher - 1] += 2;
        answer += 1;
        higher -= 1;
      }
      counts[bit] -= 1;
    }
    counts[bit + 1] += Math.floor(counts[bit] / 2);
  }
  return answer;
}

const minOperations = solve;
class Solution {
  minOperations(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
