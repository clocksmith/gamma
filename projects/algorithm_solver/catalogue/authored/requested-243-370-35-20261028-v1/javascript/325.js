"use strict";

function solve(nums, k) {
  const first = new Map([[0, -1]]);
  let cur = 0;
  let best = 0;
  for (let i = 0; i < nums.length; i++) {
    cur += nums[i];
    if (first.has(cur - k)) {
      const len = i - first.get(cur - k);
      if (len > best) best = len;
    }
    if (!first.has(cur)) first.set(cur, i);
  }
  return best;
}

function maxSubArrayLen(nums, k) {
  return solve(nums, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.maxSubArrayLen = maxSubArrayLen;
