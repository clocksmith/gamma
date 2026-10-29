"use strict";
// Hack2Hire 69e51800ad1522fdaff14d5f (Find Size of Largest Subset) over an INFERRED spec; qualification unknown.

function solve(arr) {
  let best = 0;
  for (let bit = 0; bit < 31; bit++) { // values stay below 2**30, so 32-bit shifts are exact
    let count = 0;
    for (const v of arr) count += (v >> bit) & 1;
    if (count > best) best = count;
  }
  return best;
}

function findLargestSubsetSize(arr) { return solve(arr); }

module.exports = solve;
module.exports.findLargestSubsetSize = findLargestSubsetSize;
