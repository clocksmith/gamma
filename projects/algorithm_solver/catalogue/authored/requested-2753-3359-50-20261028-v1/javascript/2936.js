"use strict";

function solve(nums) {
  const isArr = Array.isArray(nums);
  const n = isArr ? nums.length : nums.size();
  const getAt = isArr ? (idx) => nums[idx] : (idx) => nums.at(idx);
  let blocks = 0;
  let i = 0;
  while (i < n) {
    const val = getAt(i);
    let lo = i;
    let hi = n - 1;
    while (lo < hi) {
      const mid = Math.floor((lo + hi + 1) / 2);
      if (getAt(mid) === val) lo = mid;
      else hi = mid - 1;
    }
    blocks++;
    i = lo + 1;
  }
  return blocks;
}

function countBlocks(nums) {
  return solve(nums);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.countBlocks = countBlocks;
