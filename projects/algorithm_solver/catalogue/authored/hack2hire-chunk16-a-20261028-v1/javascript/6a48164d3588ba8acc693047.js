"use strict";
// Hack2Hire 6a48164d3588ba8acc693047 (Merge Unique Arrays) over an INFERRED spec; qualification unknown.

function solve(nums1, nums2) {
  const out = [];
  let i = 0, j = 0;
  while (i < nums1.length || j < nums2.length) {
    let value;
    if (j >= nums2.length || (i < nums1.length && nums1[i] <= nums2[j])) value = nums1[i++];
    else value = nums2[j++];
    if (out.length === 0 || out[out.length - 1] < value) out.push(value);
  }
  return out;
}

function mergeUnique(nums1, nums2) { return solve(nums1, nums2); }

module.exports = solve;
module.exports.mergeUnique = mergeUnique;
