"use strict";
// Hack2Hire 68c2d9291f64f4312b0a3df2 (Find Median In Large Array) over an INFERRED spec; qualification unknown.

function solve(nums) {
  let state = 20261029;
  // Park-Miller generator; products stay below 2**47 so Number arithmetic is exact
  const draw = (m) => { state = (state * 48271) % 2147483647; return state % m; };
  const select = (values, k) => { // quickselect with three-way partitioning on fresh arrays
    for (;;) {
      const pivot = values[draw(values.length)];
      const lows = values.filter((x) => x < pivot);
      if (k < lows.length) { values = lows; continue; }
      const highs = values.filter((x) => x > pivot);
      const belowHighs = values.length - highs.length;
      if (k >= belowHighs) { values = highs; k -= belowHighs; continue; }
      return pivot;
    }
  };
  const n = nums.length;
  if (n % 2) return select(nums, (n - 1) / 2);
  const total = select(nums, n / 2 - 1) + select(nums, n / 2);
  return total / 2; // an integer when exact, otherwise a half-integer (both exact in a double)
}

function findMedian(nums) { return solve(nums); }

module.exports = solve;
module.exports.findMedian = findMedian;
