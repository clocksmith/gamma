"use strict";

function spf(x) {
  if ((x & 1) === 0) return 2;
  for (let d = 3; d * d <= x; d += 2) {
    if (x % d === 0) return d;
  }
  return x;
}

function solve(nums) {
  const arr = nums.slice();
  let ops = 0;
  for (let i = arr.length - 2; i >= 0; i--) {
    if (arr[i] > arr[i + 1]) {
      arr[i] = spf(arr[i]);
      ops++;
      if (arr[i] > arr[i + 1]) return -1;
    }
  }
  return ops;
}

function minOperations(nums) {
  return solve(nums);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minOperations = minOperations;
