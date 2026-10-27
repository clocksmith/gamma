'use strict';

// 4031. Find All Numbers Disappeared in an Array II.
// Specification: https://leetcode.com/problems/find-all-numbers-disappeared-in-an-array-ii/description/
// O(n log n) time and O(n) space; return maximal inclusive missing ranges. Inputs are preserved.
function solve(nums, lower, upper) {
  const values = [...new Set(nums.filter(value => value >= lower && value <= upper))].sort((a, b) => a - b);
  const answer = [];
  let next = lower;
  for (const value of values) {
    if (next < value) answer.push([next, value - 1]);
    next = value + 1;
  }
  if (next <= upper) answer.push([next, upper]);
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
