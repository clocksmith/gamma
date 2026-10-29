"use strict";

function solve(nums, k) {
  let lo = nums[0], hi = 0;
  for (let i = 0; i < nums.length; i++) {
    if (nums[i] < lo) lo = nums[i];
    hi += nums[i];
  }
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    let cnt = 0, cur = 0, left = 0;
    for (let right = 0; right < nums.length; right++) {
      cur += nums[right];
      while (cur > mid) cur -= nums[left++];
      cnt += right - left + 1;
    }
    if (cnt >= k) hi = mid;
    else lo = mid + 1;
  }
  return lo;
}

function kthSmallestSubarraySum(nums, k) {
  return solve(nums, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.kthSmallestSubarraySum = kthSmallestSubarraySum;
