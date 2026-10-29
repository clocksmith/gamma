"use strict";
// Hack2Hire 67e08fffa59c3d249d3625e0 (Count Distinct Elements in Window) over an INFERRED spec; qualification unknown.

function solve(nums, k) {
  const counts = new Map(), out = [];
  let distinct = 0;
  for (let i = 0; i < nums.length; i++) {
    const c = counts.get(nums[i]) || 0;
    if (c === 0) distinct++;
    counts.set(nums[i], c + 1);
    if (i >= k) {
      const old = nums[i - k], left = counts.get(old) - 1;
      counts.set(old, left);
      if (left === 0) distinct--;
    }
    if (i >= k - 1) out.push(distinct);
  }
  return out;
}

function countDistinct(nums, k) { return solve(nums, k); }

module.exports = solve;
module.exports.countDistinct = countDistinct;
