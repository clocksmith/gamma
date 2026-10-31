"use strict";

function solve(nums, queries) {
  const n = nums.length;
  const diff = new Int32Array(n + 1);
  for (let i = 0; i < queries.length; i++) {
    diff[queries[i][0]]++;
    diff[queries[i][1] + 1]--;
  }
  let cur = 0;
  for (let i = 0; i < n; i++) {
    cur += diff[i];
    if (cur < nums[i]) return false;
  }
  return true;
}

function isZeroArray(nums, queries) {
  return solve(nums, queries);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.isZeroArray = isZeroArray;
