'use strict';

// 1399. Count Largest Group (Easy).
// Specification: https://leetcode.com/problems/count-largest-group/description/
// O(n * d) time, O(d) space; d is the decimal digit count of n.
function solve(n) {
  const counts = new Map();
  let largest = 0;
  for (let value = 1; value <= n; value++) {
    let remaining = value;
    let digitSum = 0;
    while (remaining > 0) {
      digitSum += remaining % 10;
      remaining = Math.floor(remaining / 10);
    }
    const count = (counts.get(digitSum) || 0) + 1;
    counts.set(digitSum, count);
    largest = Math.max(largest, count);
  }
  let result = 0;
  for (const count of counts.values()) {
    if (count === largest) result++;
  }
  return result;
}

const countLargestGroup = solve;
class Solution {
  countLargestGroup(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countLargestGroup };
