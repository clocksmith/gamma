"use strict";
// Hack2Hire 69efd6f096981f58ae1f6dcf (Check Prefix Permutation) over an INFERRED spec; qualification unknown.

function solve(p) {
  const n = p.length, position = new Array(n + 1).fill(0);
  for (let i = 0; i < n; i++) position[p[i]] = i;
  let low = position[1], high = position[1];
  const result = [];
  for (let k = 1; k <= n; k++) {
    const x = position[k];
    if (x < low) low = x;
    if (x > high) high = x;
    result.push(high - low + 1 === k);
  }
  return result;
}

function prefixPermutations(p) { return solve(p); }

module.exports = solve;
module.exports.prefixPermutations = prefixPermutations;
