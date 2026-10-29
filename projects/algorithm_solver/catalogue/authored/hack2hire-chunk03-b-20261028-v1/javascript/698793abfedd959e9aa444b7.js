"use strict";
// Hack2Hire 698793abfedd959e9aa444b7 (Minimum Operations to Reduce to Zero) over an INFERRED spec; qualification unknown.

function solve(n) {
  let steps = 0;
  while (n > 0) {
    if (n % 2 === 0) n /= 2;
    else if (n === 1 || n === 3 || n % 4 === 1) n -= 1;
    else n += 1;
    steps++;
  }
  return steps;
}

function minOperations(n) { return solve(n); }

module.exports = solve;
module.exports.minOperations = minOperations;
