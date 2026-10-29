"use strict";
// Hack2Hire 6a73ba2dd713d873ca7a77a1 (Largest Number by Parity Swaps) over an INFERRED spec; qualification unknown.

function solve(num) {
  const out = [], n = num.length;
  let i = 0;
  while (i < n) {
    const parity = num.charCodeAt(i) & 1, count = new Array(10).fill(0);
    let j = i;
    while (j < n && (num.charCodeAt(j) & 1) === parity) { count[num.charCodeAt(j) - 48]++; j++; }
    for (let d = 9; d >= 0; d--) if (count[d]) out.push(String(d).repeat(count[d]));
    i = j;
  }
  return out.join("");
}

function largestByParitySwaps(num) { return solve(num); }

module.exports = solve;
module.exports.largestByParitySwaps = largestByParitySwaps;
