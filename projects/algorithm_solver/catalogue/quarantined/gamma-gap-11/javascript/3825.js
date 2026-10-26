'use strict';

// 3825. Longest Strictly Increasing Subsequence With Non-Zero Bitwise AND.
// O(B n log n) time and O(n) space, B=30; compute strict LIS separately for every possible common bit.
function solve(nums) {
  let answer = 0;
  for (let bit = 0; bit < 30; bit += 1) {
    const mask = 2 ** bit;
    const tails = [];
    for (const value of nums) {
      if ((value & mask) === 0) continue;
      let low = 0;
      let high = tails.length;
      while (low < high) {
        const middle = Math.floor((low + high) / 2);
        if (tails[middle] < value) low = middle + 1;
        else high = middle;
      }
      tails[low] = value;
    }
    answer = Math.max(answer, tails.length);
  }
  return answer;
}

const longestSubsequence = solve;
class Solution {
  longestSubsequence(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSubsequence };
