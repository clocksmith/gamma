'use strict';

// 442. Find All Duplicates in an Array. Temporary sign marks use O(1) auxiliary space; restore all input values before returning.

function solve(nums) {
  const answer = [];
  for (let i = 0; i < nums.length; i += 1) {
    const value = Math.abs(nums[i]);
    if (nums[value - 1] < 0) answer.push(value);
    else nums[value - 1] = -nums[value - 1];
  }
  for (let i = 0; i < nums.length; i += 1) nums[i] = Math.abs(nums[i]);
  return answer;
}

const findDuplicates = solve;
class Solution {
  findDuplicates(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDuplicates };
