'use strict';

// 2354. Number of Excellent Pairs. Count ordered value pairs after deduplication by population count; O(n*B+B^2) time and O(n+B) space, B=31. Inputs are preserved.

function solve(nums, k) {
  const counts = Array(32).fill(0);
  for (let value of new Set(nums)) {
    let bits = 0;
    while (value > 0) {
      value &= value - 1;
      bits += 1;
    }
    counts[bits] += 1;
  }
  let answer = 0;
  for (let first = 0; first < 32; first += 1) {
    for (let second = Math.max(0, k - first); second < 32; second += 1) {
      answer += counts[first] * counts[second];
    }
  }
  return answer;
}

const countExcellentPairs = solve;
class Solution {
  countExcellentPairs(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countExcellentPairs };
