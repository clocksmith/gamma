"use strict";

function solve(nums, a, b, c) {
  const n = nums.length;
  const res = new Array(n);
  let l = 0, r = n - 1;
  let idx = a >= 0 ? n - 1 : 0;
  while (l <= r) {
    const vl = a * nums[l] * nums[l] + b * nums[l] + c;
    const vr = a * nums[r] * nums[r] + b * nums[r] + c;
    if (a >= 0) {
      if (vl > vr) {
        res[idx--] = vl;
        l++;
      } else {
        res[idx--] = vr;
        r--;
      }
    } else {
      if (vl < vr) {
        res[idx++] = vl;
        l++;
      } else {
        res[idx++] = vr;
        r--;
      }
    }
  }
  return res;
}

function sortTransformedArray(nums, a, b, c) {
  return solve(nums, a, b, c);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.sortTransformedArray = sortTransformedArray;
