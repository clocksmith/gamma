'use strict';

// 3881. Direction Assignments with Exactly K Visible People.
// O(min(k,n-1-k) + log MOD) modular steps and O(1) space; choose visible people and either direction for pos.
function solve(n, pos, k) {
  const modulus = 1000000007n;
  const chosen = Math.min(k, n - 1 - k);
  let numerator = 1n;
  let denominator = 1n;
  for (let index = 1; index <= chosen; index += 1) {
    numerator = numerator * BigInt(n - index) % modulus;
    denominator = denominator * BigInt(index) % modulus;
  }
  let inverse = 1n;
  let exponent = 1000000005;
  while (exponent > 0) {
    if (exponent % 2 === 1) inverse = inverse * denominator % modulus;
    denominator = denominator * denominator % modulus;
    exponent = Math.floor(exponent / 2);
  }
  return Number(2n * numerator * inverse % modulus);
}

const countAssignments = solve;
class Solution {
  countAssignments(n, pos, k) { return solve(n, pos, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countAssignments };
