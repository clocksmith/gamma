"use strict";
// Hack2Hire 6a14d69a7b0582b352787fa8 (Jumping by Height) over an INFERRED spec; qualification unknown.

function solve(nums, index) {
  const n = nums.length;
  const seen = new Set(); // states 2 * position + (1 when the next jump goes left)
  let position = index, height = nums[index], left = true, jumps = 0;
  for (;;) {
    const state = 2 * position + (left ? 1 : 0);
    if (seen.has(state)) return -1;
    seen.add(state);
    const target = left ? position - height : position + height;
    if (target < 0 || target >= n) return jumps;
    position = target; height = nums[target]; left = !left; jumps++;
  }
}

function countJumps(nums, index) { return solve(nums, index); }

module.exports = solve;
module.exports.countJumps = countJumps;
