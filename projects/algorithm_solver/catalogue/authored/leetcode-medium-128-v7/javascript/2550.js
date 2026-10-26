'use strict';

// 2550. Count Collisions of Monkeys on a Polygon: subtract the two collision-free directions from all binary choices.
// O(log n) modular operations and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(n) {
  const modulus = 1000000007n;
  let base = 2n;
  let exponent = n;
  let result = 1n;
  while (exponent > 0) {
    if (exponent % 2 === 1) result = result * base % modulus;
    base = base * base % modulus;
    exponent = Math.floor(exponent / 2);
  }
  return Number((result - 2n + modulus) % modulus);
}

const monkeyMove = solve;
class Solution {
  monkeyMove(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, monkeyMove };
