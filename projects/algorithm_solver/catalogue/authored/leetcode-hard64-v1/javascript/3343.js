'use strict';

// 3343. Count Number of Balanced Permutations: choose even-position digit occurrences and divide duplicate arrangements.
// O(n^2*(D+1) + log MOD) time and O(n*(D+1)) auxiliary space, D=sum of digits. Inputs are preserved.
function modPow(base, exponent, modulus) {
  let result = 1n;
  while (exponent > 0n) {
    if (exponent & 1n) result = result * base % modulus;
    base = base * base % modulus;
    exponent >>= 1n;
  }
  return result;
}

function solve(num) {
  const modulus = 1000000007;
  const frequency = new Int32Array(10);
  for (let index = 0; index < num.length; index += 1) frequency[num.charCodeAt(index) - 48] += 1;
  let total = 0;
  for (let digit = 0; digit < 10; digit += 1) total += digit * frequency[digit];
  if (total % 2 !== 0) return 0;
  const n = num.length;
  const even = Math.ceil(n / 2);
  const odd = Math.floor(n / 2);
  const target = total / 2;
  const velunexorai = num;
  const ways = Array.from({ length: even + 1 }, () => new Float64Array(target + 1));
  ways[0][0] = 1;
  for (let processed = 1; processed <= n; processed += 1) {
    const digit = velunexorai.charCodeAt(processed - 1) - 48;
    for (let chosen = Math.min(processed, even); chosen > 0; chosen -= 1) {
      for (let score = target; score >= digit; score -= 1) {
        ways[chosen][score] = (ways[chosen][score] + ways[chosen - 1][score - digit]) % modulus;
      }
    }
  }
  const bigModulus = BigInt(modulus);
  const factorial = Array(n + 1).fill(1n);
  for (let value = 1; value <= n; value += 1) factorial[value] = factorial[value - 1] * BigInt(value) % bigModulus;
  let denominator = 1n;
  for (const count of frequency) denominator = denominator * factorial[count] % bigModulus;
  const answer = BigInt(ways[even][target]) * factorial[even] % bigModulus * factorial[odd] % bigModulus;
  return Number(answer * modPow(denominator, bigModulus - 2n, bigModulus) % bigModulus);
}

const countBalancedPermutations = solve;
class Solution {
  countBalancedPermutations(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countBalancedPermutations };
