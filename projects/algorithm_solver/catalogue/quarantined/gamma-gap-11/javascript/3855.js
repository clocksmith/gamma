'use strict';

// 3855. Sum of K-Digit Numbers in a Range.
// O(log k) modular steps and O(1) auxiliary space; exact modular multiplication, including leading zeros.
function solve(l, r, k) {
  const modulus = 1000000007n;
  function power(base, exponent) {
    let result = 1n;
    while (exponent > 0) {
      if (exponent % 2 === 1) result = result * base % modulus;
      base = base * base % modulus;
      exponent = Math.floor(exponent / 2);
    }
    return result;
  }
  const choices = BigInt(r - l + 1);
  const digitSum = BigInt((l + r) * (r - l + 1) / 2);
  const repunit = (power(10n, k) - 1n + modulus) * power(9n, 1000000005) % modulus;
  return Number(digitSum * power(choices, k - 1) % modulus * repunit % modulus);
}

const sumOfNumbers = solve;
class Solution {
  sumOfNumbers(l, r, k) { return solve(l, r, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfNumbers };
