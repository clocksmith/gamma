"use strict";
// Hack2Hire 67db949600e020b60078a44d (Split Array with Equal Sum) over an INFERRED spec; qualification unknown.

function solve(nums) {
  let total = 0;
  for (const v of nums) total += v;
  let prefix = 0;
  for (let i = 0; i + 1 < nums.length; i++) {
    prefix += nums[i];
    if (2 * prefix === total) return i;
    if (2 * prefix > total) break;
  }
  return -1;
}

function findSplitIndex(nums) { return solve(nums); }

module.exports = solve;
module.exports.findSplitIndex = findSplitIndex;
