"use strict";

function solve(nums) {
  const arr = nums.slice();
  for (let i = 0; i < arr.length - 1; i++) {
    if (((i & 1) === 0 && arr[i] > arr[i + 1]) || ((i & 1) === 1 && arr[i] < arr[i + 1])) {
      const tmp = arr[i];
      arr[i] = arr[i + 1];
      arr[i + 1] = tmp;
    }
  }
  return arr;
}

// Official LeetCode ABI (in_place_arg 0): rewrites nums in place and returns
// nothing. The element-wise copy of the pure result is charged as O(n) time
// and O(n) auxiliary space (the intermediate array from solve).
function wiggleSort(nums) {
  const out = solve(nums);
  for (let i = 0; i < out.length; i++) nums[i] = out[i];
}

module.exports = solve;
module.exports.solve = solve;
module.exports.wiggleSort = wiggleSort;
if (typeof Solution !== "undefined") solve.Solution = Solution;
