"use strict";
// Hack2Hire 688baac33867670cfb894157 (Longest Circular Sequence of Ones) over an INFERRED spec; qualification unknown.

function solve(nums, k) {
  const n = nums.length;
  let zeros = 0;
  for (const x of nums) if (x === 0) zeros++;
  if (zeros <= k) return n;
  let best = 0, left = 0;
  zeros = 0;
  for (let right = 0; right < 2 * n; right++) {
    if (nums[right % n] === 0) zeros++;
    while (zeros > k) { if (nums[left % n] === 0) zeros--; left++; }
    if (right - left + 1 > best) best = right - left + 1;
  }
  return best;
}

function longestCircularOnes(nums, k) { return solve(nums, k); }

module.exports = solve;
module.exports.longestCircularOnes = longestCircularOnes;
