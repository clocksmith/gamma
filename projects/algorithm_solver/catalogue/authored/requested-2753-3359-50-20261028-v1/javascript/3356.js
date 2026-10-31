"use strict";

function solve(nums, queries) {
  const n = nums.length;
  const diff = new Float64Array(n + 1);
  let cur = 0;
  let k = 0;
  for (let i = 0; i < n; i++) {
    while (cur + diff[i] < nums[i]) {
      if (k === queries.length) return -1;
      const [l, r, val] = queries[k++];
      if (r >= i) {
        diff[l > i ? l : i] += val;
        diff[r + 1] -= val;
      }
    }
    cur += diff[i];
  }
  return k;
}

function minZeroArray(nums, queries) {
  return solve(nums, queries);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minZeroArray = minZeroArray;
