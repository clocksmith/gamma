"use strict";

function solve(nums) {
  let ans = 0;
  let mx = 0;
  for (let i = nums.length - 1; i > 0; i--) {
    if (nums[i] > mx) mx = nums[i];
    ans += mx;
  }
  return ans;
}

function maxScore(nums) {
  return solve(nums);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.maxScore = maxScore;
