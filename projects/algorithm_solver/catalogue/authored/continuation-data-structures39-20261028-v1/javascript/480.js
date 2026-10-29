"use strict";

function lowerBound(arr, target) {
  let low = 0, high = arr.length;
  while (low < high) {
    const mid = (low + high) >> 1;
    if (arr[mid] < target) low = mid + 1;
    else high = mid;
  }
  return low;
}

function solve(nums, k) {
  const window = nums.slice(0, k).sort((a, b) => a - b);
  const half = k >> 1;
  const odd = (k & 1) === 1;
  const out = [odd ? window[half] : (window[half - 1] + window[half]) / 2.0];
  for (let i = k; i < nums.length; i++) {
    const removeIdx = lowerBound(window, nums[i - k]);
    window.splice(removeIdx, 1);
    const insertIdx = lowerBound(window, nums[i]);
    window.splice(insertIdx, 0, nums[i]);
    out.push(odd ? window[half] : (window[half - 1] + window[half]) / 2.0);
  }
  return out;
}

function medianSlidingWindow(nums, k) {
  return solve(nums, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.medianSlidingWindow = medianSlidingWindow;
