"use strict";
// Hack2Hire 67a25626c5f86173882e3d8f (Find Minimum Operations) over an INFERRED spec; qualification unknown.

function solve(image) {
  // the target is image reversed: target[j] === image[n - 1 - j]
  const n = image.length;
  let matched = 0;
  for (let i = 0; i < n; i++) if (image[i] === image[n - 1 - matched]) matched++;
  return n - matched;
}

function findMinimumOperations(image) { return solve(image); }

module.exports = solve;
module.exports.findMinimumOperations = findMinimumOperations;
