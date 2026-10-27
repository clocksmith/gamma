'use strict';

// 3918. Sum of Primes Between Number and Its Reverse.
// Specification: https://leetcode.com/problems/sum-of-primes-between-number-and-its-reverse/description/
// O(V log log V) time and O(V) space, V=max(n, reverse(n)). Inputs are preserved.
function solve(n) {
  const reversed = Number(String(n).split('').reverse().join(''));
  const low = Math.min(n, reversed);
  const high = Math.max(n, reversed);
  const composite = new Uint8Array(high + 1);
  for (let prime = 2; prime * prime <= high; prime++) {
    if (!composite[prime]) for (let multiple = prime * prime; multiple <= high; multiple += prime) composite[multiple] = 1;
  }
  let answer = 0;
  for (let value = Math.max(2, low); value <= high; value++) if (!composite[value]) answer += value;
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
