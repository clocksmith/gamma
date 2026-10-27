'use strict';
// 278. First Bad Version.
function solve(n, isBadVersionFn = globalThis.isBadVersion) {
  let left = 1; let right = n;
  while (left < right) {
    const middle = Math.floor((left + right) / 2);
    if (isBadVersionFn(middle)) right = middle; else left = middle + 1;
  }
  return left;
}
class Solution { firstBadVersion(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution };
