"use strict";
// Hack2Hire 68f842c4d7ff180d0ab950eb (Minimum Swaps to Group Evens First) over an INFERRED spec; qualification unknown.

function solve(nums) {
  let evens = 0;
  for (const v of nums) if (v % 2 === 0) evens++;
  let swaps = 0;
  for (let i = 0; i < evens; i++) if (nums[i] % 2 !== 0) swaps++;
  return swaps;
}

function minSwaps(nums) { return solve(nums); }

module.exports = solve;
module.exports.minSwaps = minSwaps;
