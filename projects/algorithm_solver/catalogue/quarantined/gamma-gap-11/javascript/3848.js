'use strict';

// 3848. Check Digitorial Permutation.
// O(d) time and O(1) alphabet space; the factorial sum is invariant under all digit permutations.
function solve(n) {
  const factorials = Array(10).fill(1);
  for (let digit = 1; digit < 10; digit += 1) factorials[digit] = factorials[digit - 1] * digit;
  const digits = Array(10).fill(0);
  let value = 0;
  for (const char of String(n)) {
    const digit = Number(char);
    digits[digit] += 1;
    value += factorials[digit];
  }
  for (const char of String(value)) digits[Number(char)] -= 1;
  return digits.every(count => count === 0);
}

const isDigitorialPermutation = solve;
class Solution {
  isDigitorialPermutation(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isDigitorialPermutation };
