"use strict";
// Hack2Hire 6789754f11318cc872dd83ec (Find Greatest Triple) over an INFERRED spec; qualification unknown.

function solve(digits) {
  // three places; place p must leave (2 - p) digits after its pick
  const n = digits.length;
  let value = 0, start = 0;
  for (let place = 0; place < 3; place++) {
    const end = n - (2 - place);
    let best = start;
    for (let i = start + 1; i < end; i++) if (digits[i] > digits[best]) best = i; // strict > keeps the leftmost maximum
    value = value * 10 + digits[best];
    start = best + 1;
  }
  return value;
}

function findGreatestTriple(digits) { return solve(digits); }

module.exports = solve;
module.exports.findGreatestTriple = findGreatestTriple;
