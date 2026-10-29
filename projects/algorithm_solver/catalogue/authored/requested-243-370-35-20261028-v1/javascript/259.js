"use strict";

function solve(nums, target) {
  const arr = nums.slice().sort((a, b) => a - b);
  const n = arr.length;
  let ans = 0;
  for (let i = 0; i < n - 2; i++) {
    let lo = i + 1, hi = n - 1;
    while (lo < hi) {
      if (arr[i] + arr[lo] + arr[hi] < target) {
        ans += hi - lo;
        lo++;
      } else {
        hi--;
      }
    }
  }
  return ans;
}

function threeSumSmaller(nums, target) {
  return solve(nums, target);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.threeSumSmaller = threeSumSmaller;
