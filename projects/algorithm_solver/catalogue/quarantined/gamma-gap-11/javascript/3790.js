'use strict';

// 3790. Smallest All-Ones Multiple.
// O(k) time and O(1) space; iterate remainders without constructing the large decimal integer.
function solve(k) {
  if (k % 2 === 0 || k % 5 === 0) return -1;
  let remainder = 0;
  for (let length = 1; length <= k; length += 1) {
    remainder = (remainder * 10 + 1) % k;
    if (remainder === 0) return length;
  }
  return -1;
}

const minAllOneMultiple = solve;
class Solution {
  minAllOneMultiple(k) { return solve(k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minAllOneMultiple };
