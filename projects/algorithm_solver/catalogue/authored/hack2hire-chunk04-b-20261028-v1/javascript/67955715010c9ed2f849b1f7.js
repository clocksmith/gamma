"use strict";
// Hack2Hire 67955715010c9ed2f849b1f7 (Binary Search Variation) over an INFERRED spec; qualification unknown.

function solve(arr, target) {
  let lo = 0, hi = arr.length;
  while (lo < hi) {
    const mid = (lo + hi) >>> 1;
    if (arr[mid] < target) lo = mid + 1;
    else hi = mid;
  }
  if (lo < arr.length && arr[lo] === target) return lo;
  return lo - 1;
}

function binarySearch(arr, target) { return solve(arr, target); }

module.exports = solve;
module.exports.binarySearch = binarySearch;
