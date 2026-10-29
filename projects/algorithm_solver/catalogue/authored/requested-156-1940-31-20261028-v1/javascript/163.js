"use strict";

function solve(nums, lower, upper) {
  const res = [];
  let prev = lower - 1;
  for (let i = 0; i < nums.length; i++) {
    const x = nums[i];
    if (x - prev >= 2) res.push([prev + 1, x - 1]);
    prev = x;
  }
  if (upper + 1 - prev >= 2) res.push([prev + 1, upper]);
  return res;
}

function findMissingRanges(nums, lower, upper) {
  return solve(nums, lower, upper);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.findMissingRanges = findMissingRanges;
