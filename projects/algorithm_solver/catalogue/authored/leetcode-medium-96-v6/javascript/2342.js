'use strict';

// 2342. Max Sum of a Pair With Equal Sum of Digits: retain the largest earlier number for every decimal digit sum.
// O(n d) time and O(d) auxiliary entries for at most d decimal digits; inputs are read-only.
function solve(nums) {
  const largest = new Map();
  let answer = -1;
  for (const value of nums) {
    let remaining = value;
    let digitSum = 0;
    while (remaining > 0) {
      digitSum += remaining % 10;
      remaining = Math.floor(remaining / 10);
    }
    if (largest.has(digitSum)) answer = Math.max(answer, value + largest.get(digitSum));
    largest.set(digitSum, Math.max(value, largest.has(digitSum) ? largest.get(digitSum) : value));
  }
  return answer;
}

const maximumSum = solve;
class Solution {
  maximumSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumSum };
