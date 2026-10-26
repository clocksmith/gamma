'use strict';

// 2507. Smallest Value After Replacing With Sum of Prime Factors: repeat prime-factor summation until the value reaches a fixed point.
// O(sqrt(n) * log(n + 1)) time and O(1) auxiliary space; inputs are read-only.
function solve(n) {
  let value = n;
  while (true) {
    let remaining = value;
    let total = 0;
    for (let factor = 2; factor * factor <= remaining; factor += 1) {
      while (remaining % factor === 0) {
        total += factor;
        remaining /= factor;
      }
    }
    if (remaining > 1) total += remaining;
    if (total === value) return value;
    value = total;
  }
}

const smallestValue = solve;
class Solution {
  smallestValue(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestValue };
