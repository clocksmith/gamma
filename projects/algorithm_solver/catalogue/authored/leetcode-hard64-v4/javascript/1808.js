'use strict';

// 1808. Maximize Number of Nice Divisors. Optimal integer partition into threes and twos; O(log primeFactors) modular operations. Inputs are preserved.

function solve(primeFactors) {
  if (primeFactors <= 3) return primeFactors;
  const modulus = 1000000007n;
  function power(exponent) {
    let base = 3n;
    let result = 1n;
    while (exponent > 0) {
      if (exponent % 2 === 1) result = result * base % modulus;
      base = base * base % modulus;
      exponent = Math.floor(exponent / 2);
    }
    return result;
  }
  const quotient = Math.floor(primeFactors / 3);
  const remainder = primeFactors % 3;
  if (remainder === 0) return Number(power(quotient));
  if (remainder === 1) return Number(power(quotient - 1) * 4n % modulus);
  return Number(power(quotient) * 2n % modulus);
}

const maxNiceDivisors = solve;
class Solution {
  maxNiceDivisors(primeFactors) { return solve(primeFactors); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxNiceDivisors };
