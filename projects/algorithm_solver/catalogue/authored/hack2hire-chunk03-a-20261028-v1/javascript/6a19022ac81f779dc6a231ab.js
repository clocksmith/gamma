"use strict";
// Hack2Hire 6a19022ac81f779dc6a231ab (Match Cyclic Shift to Descending Sequence) over an INFERRED spec; qualification unknown.

function solve(nums) {
  const n = nums.length;
  let ascent = -1, count = 0;
  for (let i = 0; i < n; i++) {
    if (nums[i] < nums[(i + 1) % n]) {
      count++;
      ascent = i;
      if (count > 1) return -1;
    }
  }
  if (count === 0) return 0;
  return (n - (ascent + 1)) % n;
}

function findDescendingShift(nums) { return solve(nums); }

module.exports = solve;
module.exports.findDescendingShift = findDescendingShift;
