"use strict";
// Hack2Hire 6910e7e971ea59cda5a81ac4 (Largest K Elements in Sliding Window) over an INFERRED spec; qualification unknown.

function lowerBound(a, x) {
  let lo = 0, hi = a.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (a[mid] < x) lo = mid + 1; else hi = mid; }
  return lo;
}

function solve(nums, k, w) {
  const window = nums.slice(0, w).sort((p, q) => p - q);
  const top = () => window.slice(w - k).reverse();
  const out = [top()];
  for (let i = w; i < nums.length; i++) {
    window.splice(lowerBound(window, nums[i - w]), 1);
    window.splice(lowerBound(window, nums[i]), 0, nums[i]);
    out.push(top());
  }
  return out;
}

function largestKInWindows(nums, k, w) { return solve(nums, k, w); }

module.exports = solve;
module.exports.largestKInWindows = largestKInWindows;
