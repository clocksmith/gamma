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

function wiggleSort(nums) {
  return solve(nums);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.wiggleSort = wiggleSort;
