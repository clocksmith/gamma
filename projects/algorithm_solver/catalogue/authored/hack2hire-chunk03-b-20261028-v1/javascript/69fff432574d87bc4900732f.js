"use strict";
// Hack2Hire 69fff432574d87bc4900732f (Minimum Steps to Reorder Layers) over an INFERRED spec; qualification unknown.

function solve(current, desired) {
  const position = new Map();
  desired.forEach((v, i) => position.set(v, i));
  let kept = 1;
  while (kept < current.length && position.get(current[kept]) > position.get(current[kept - 1])) kept++;
  return current.length - kept;
}

function minOperations(current, desired) { return solve(current, desired); }

module.exports = solve;
module.exports.minOperations = minOperations;
