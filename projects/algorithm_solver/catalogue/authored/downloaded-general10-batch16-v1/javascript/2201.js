'use strict';

// 2201. Count Artifacts That Can Be Extracted (Medium).
// Specification: https://leetcode.com/problems/count-artifacts-that-can-be-extracted/description/
function solve(n, artifacts, dig) {
  const dug = new Set(dig.map((c) => c[0] + ',' + c[1]));
  let count = 0;
  for (const art of artifacts) {
    let ok = true;
    for (let r = art[0]; r <= art[2] && ok; r++) {
      for (let c = art[1]; c <= art[3]; c++) {
        if (!dug.has(r + ',' + c)) { ok = false; break; }
      }
    }
    if (ok) count++;
  }
  return count;
}
const digArtifacts = solve;
class Solution { digArtifacts(n, artifacts, dig) { return solve(n, artifacts, dig); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, digArtifacts };
