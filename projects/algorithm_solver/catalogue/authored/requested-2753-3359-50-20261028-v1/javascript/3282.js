"use strict";

function solve(nums) {
  let ans = 0;
  let mx = 0;
  for (let i = 0; i < nums.length - 1; i++) {
    if (nums[i] > mx) mx = nums[i];
    ans += mx;
  }
  return ans;
}

function findMaximumScore(nums) {
  return solve(nums);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.findMaximumScore = findMaximumScore;
