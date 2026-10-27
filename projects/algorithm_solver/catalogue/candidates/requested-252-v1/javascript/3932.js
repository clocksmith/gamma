'use strict';

// 3932. Count K-th Roots in a Range.
// Specification: https://leetcode.com/problems/count-k-th-roots-in-a-range/description/
// O(k log(r+2)) time and O(1) space; exact integer root comparison, including zero. Inputs are preserved.
function solve(l, r, k) {
  function floorRoot(bound) {
    if (bound < 0) return -1;
    if (k === 1 || bound < 2) return bound;
    function fits(base) {
      let product = 1;
      for (let step = 0; step < k; step++) {
        if (base !== 0 && product > Math.floor(bound / base)) return false;
        product *= base;
      }
      return true;
    }
    let low = 0;
    let high = bound + 1;
    while (low + 1 < high) {
      const middle = Math.floor((low + high) / 2);
      if (fits(middle)) low = middle; else high = middle;
    }
    return low;
  }
  return floorRoot(r) - floorRoot(l - 1);
}

if (typeof module !== 'undefined') module.exports = { solve };
