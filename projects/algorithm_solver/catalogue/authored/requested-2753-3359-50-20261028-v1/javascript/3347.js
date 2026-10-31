"use strict";

function lowerBound(arr, target) {
  let lo = 0, hi = arr.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] < target) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

function upperBound(arr, target) {
  let lo = 0, hi = arr.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] <= target) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

function solve(nums, k, numOperations) {
  const arr = nums.slice().sort((a, b) => a - b);
  const n = arr.length;
  const freq = new Map();
  for (let i = 0; i < n; i++) freq.set(arr[i], (freq.get(arr[i]) || 0) + 1);
  let ans = 0;
  let r = 0;
  for (let l = 0; l < n; l++) {
    while (r < n && arr[r] - arr[l] <= 2 * k) r++;
    const can = r - l < numOperations ? r - l : numOperations;
    if (can > ans) ans = can;
  }
  for (const [v, c] of freq.entries()) {
    const lo = lowerBound(arr, v - k);
    const hi = upperBound(arr, v + k);
    const can = hi - lo < c + numOperations ? hi - lo : c + numOperations;
    if (can > ans) ans = can;
  }
  return ans;
}

function maxFrequency(nums, k, numOperations) {
  return solve(nums, k, numOperations);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.maxFrequency = maxFrequency;
