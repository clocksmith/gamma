"use strict";
// Hack2Hire 6a31cf175117d1b543567dcc (Merge Values into Blocks) over an INFERRED spec; qualification unknown.

function solve(arr) {
  const last = new Map();
  for (let i = 0; i < arr.length; i++) last.set(arr[i], i);
  let pieces = 0;
  let reach = -1;
  for (let i = 0; i < arr.length; i++) {
    const end = last.get(arr[i]);
    if (end > reach) reach = end;
    if (reach === i) pieces++;
  }
  return last.size - pieces;
}

function minOperations(arr) { return solve(arr); }

module.exports = solve;
module.exports.minOperations = minOperations;
