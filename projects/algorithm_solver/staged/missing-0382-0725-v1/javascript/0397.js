'use strict';

// 397. Integer Replacement. Greedily clear low bits; avoid signed 32-bit overflow in JavaScript.

function solve(n) {
  let steps = 0;
  while (n > 1) {
    if (n % 2 === 0) n /= 2;
    else if (n === 3 || n % 4 === 1) n -= 1;
    else n += 1;
    steps += 1;
  }
  return steps;
}

const integerReplacement = solve;
class Solution {
  integerReplacement(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, integerReplacement };
