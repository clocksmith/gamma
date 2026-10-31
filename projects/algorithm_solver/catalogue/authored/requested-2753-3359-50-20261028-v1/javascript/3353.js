"use strict";

function solve(nums) {
  let ops = 0;
  for (let i = 0; i < nums.length - 1; i++) {
    if (nums[i] !== nums[i + 1]) ops++;
  }
  return ops;
}

function minOperations(nums) {
  return solve(nums);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minOperations = minOperations;
