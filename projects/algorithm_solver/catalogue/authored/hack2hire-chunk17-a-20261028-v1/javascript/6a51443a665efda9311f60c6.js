"use strict";
// Hack2Hire 6a51443a665efda9311f60c6 (Suffix Maximum Count) over an INFERRED spec; qualification unknown.

function solve(nums, query) {
  const n = nums.length;
  const counts = new Int32Array(n);
  let best = nums[n - 1], count = 0;
  for (let i = n - 1; i >= 0; i--) {
    const v = nums[i];
    if (v > best) { best = v; count = 1; }
    else if (v === best) count++;
    counts[i] = count;
  }
  return query.map((q) => counts[q]);
}

function suffixMaxCount(nums, query) { return solve(nums, query); }

module.exports = solve;
module.exports.suffixMaxCount = suffixMaxCount;
