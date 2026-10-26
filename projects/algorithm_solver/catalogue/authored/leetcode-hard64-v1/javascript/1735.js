'use strict';

// 1735. Count Ways to Make Array With Product: prime exponents and stars-and-bars combinations.
// O(M + Q*sqrt(K) + Q*log(K)) time and O(M) space, M=max(n)+floor(log2(K)). Inputs are preserved.
function modPow(base, exponent, modulus) {
  let result = 1n;
  while (exponent > 0n) {
    if (exponent & 1n) result = result * base % modulus;
    base = base * base % modulus;
    exponent >>= 1n;
  }
  return result;
}

function solve(queries) {
  const modulus = 1000000007n;
  let maximumN = 0;
  let maximumK = 0;
  for (const [length, product] of queries) {
    maximumN = Math.max(maximumN, length);
    maximumK = Math.max(maximumK, product);
  }
  const limit = maximumN + Math.floor(Math.log2(maximumK)) + 1;
  const factorial = Array(limit + 1).fill(1n);
  for (let index = 1; index <= limit; index += 1) factorial[index] = factorial[index - 1] * BigInt(index) % modulus;
  const inverse = Array(limit + 1).fill(1n);
  inverse[limit] = modPow(factorial[limit], modulus - 2n, modulus);
  for (let index = limit; index > 0; index -= 1) inverse[index - 1] = inverse[index] * BigInt(index) % modulus;
  function choose(total, count) {
    return factorial[total] * inverse[count] % modulus * inverse[total - count] % modulus;
  }
  const answers = [];
  for (const [length, product] of queries) {
    let remaining = product;
    let ways = 1n;
    for (let prime = 2; prime * prime <= remaining; prime += 1) {
      let exponent = 0;
      while (remaining % prime === 0) {
        remaining /= prime;
        exponent += 1;
      }
      if (exponent > 0) ways = ways * choose(length + exponent - 1, exponent) % modulus;
    }
    if (remaining > 1) ways = ways * BigInt(length) % modulus;
    answers.push(Number(ways));
  }
  return answers;
}

const waysToFillArray = solve;
class Solution {
  waysToFillArray(queries) { return solve(queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, waysToFillArray };
