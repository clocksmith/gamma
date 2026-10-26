'use strict';

// 1889. Minimum Space Wasted From Packaging. Supplier sweeps over sorted packages; O(n log n + B log B + B log n) time, O(n+B) space. Inputs are preserved.

function solve(packages, boxes) {
  const modulus = 1000000007;
  const ordered = packages.slice().sort((a, b) => a - b);
  let total = 0;
  for (const value of ordered) total += value;
  let best = Infinity;
  for (const supplier of boxes) {
    const sizes = supplier.slice().sort((a, b) => a - b);
    if (sizes.length === 0 || sizes[sizes.length - 1] < ordered[ordered.length - 1]) continue;
    let cursor = 0;
    let capacity = 0;
    for (const size of sizes) {
      let left = cursor;
      let right = ordered.length;
      while (left < right) {
        const middle = Math.floor((left + right) / 2);
        if (ordered[middle] <= size) left = middle + 1;
        else right = middle;
      }
      capacity += (left - cursor) * size;
      cursor = left;
      if (cursor === ordered.length) break;
    }
    best = Math.min(best, capacity - total);
  }
  return best === Infinity ? -1 : best % modulus;
}

const minWastedSpace = solve;
class Solution {
  minWastedSpace(packages, boxes) { return solve(packages, boxes); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minWastedSpace };
