"use strict";
// Hack2Hire 69e9376dfbaf3da6418286a5 (Find Balanced Prefix in Permutation) over an INFERRED spec; qualification unknown.

function solve(p) {
  const n = p.length, pos = new Array(n + 1).fill(0);
  for (let i = 0; i < n; i++) pos[p[i]] = i;
  let lo = pos[1], hi = pos[1];
  const out = [];
  for (let k = 1; k <= n; k++) {
    lo = Math.min(lo, pos[k]); hi = Math.max(hi, pos[k]);
    out.push(hi - lo + 1 === k ? "1" : "0");
  }
  return out.join("");
}

function balancedNumbers(p) { return solve(p); }

module.exports = solve;
module.exports.balancedNumbers = balancedNumbers;
