"use strict";
// Hack2Hire 69cb2283ff3ebde766cedbdd (Valid Zero-Based Permutation Check) over an INFERRED spec; qualification unknown.

function solve(nums) {
  const a = nums.slice(); // private copy: the argument is never modified
  const n = a.length;
  let i = 0;
  while (i < n) {
    const v = a[i];
    if (v === i) i += 1;
    else if (v < 0 || v >= n || a[v] === v) return false;
    else { a[i] = a[v]; a[v] = v; }
  }
  return true;
}

function isZeroBasedPermutation(nums) { return solve(nums); }

module.exports = solve;
module.exports.isZeroBasedPermutation = isZeroBasedPermutation;
