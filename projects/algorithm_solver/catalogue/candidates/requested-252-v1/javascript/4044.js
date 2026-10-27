'use strict';

// 4044. Count Good Cyclic Rotations.
// Specification: https://leetcode.com/problems/count-good-cyclic-rotations/description/
// O(n) time and O(1) auxiliary space; first half sum must strictly exceed the second half. Inputs are preserved.
function solve(nums) {
  const half = nums.length / 2;
  let total = 0;
  let window = 0;
  for (let index = 0; index < nums.length; index++) { total += nums[index]; if (index < half) window += nums[index]; }
  let answer = 0;
  for (let start = 0; start < nums.length; start++) {
    if (window > total - window) answer++;
    window += nums[(start + half) % nums.length] - nums[start];
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
