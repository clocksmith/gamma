'use strict';

// 3671. Sum of Beautiful Subsequences.
// O(M log M + n sqrt(M) + n D log M) time, O(M log M) space; D = maximum divisor count. Uses gcd = sum of totients over divisors; inputs are preserved.
function solve(nums) {
  const modulus = 1000000007;
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  const phi = Int32Array.from({ length: maximum + 1 }, (_, index) => index);
  for (let prime = 2; prime <= maximum; prime += 1) {
    if (phi[prime] === prime) {
      for (let value = prime; value <= maximum; value += prime) phi[value] -= phi[value] / prime;
    }
  }
  const trees = new Map();
  const divisorCache = new Map();
  let answer = 0;
  for (const value of nums) {
    if (!divisorCache.has(value)) {
      const divisors = [];
      for (let divisor = 1; divisor * divisor <= value; divisor += 1) {
        if (value % divisor === 0) {
          divisors.push(divisor);
          if (divisor * divisor !== value) divisors.push(value / divisor);
        }
      }
      divisorCache.set(value, divisors);
    }
    for (const divisor of divisorCache.get(value)) {
      if (!trees.has(divisor)) trees.set(divisor, new Int32Array(Math.floor(maximum / divisor) + 1));
      const tree = trees.get(divisor);
      const coordinate = value / divisor;
      let ways = 1;
      for (let index = coordinate - 1; index > 0; index -= index & -index) ways = (ways + tree[index]) % modulus;
      for (let index = coordinate; index < tree.length; index += index & -index) tree[index] = (tree[index] + ways) % modulus;
      answer = (answer + phi[divisor] * ways) % modulus;
    }
  }
  return answer;
}

const totalBeauty = solve;
class Solution {
  totalBeauty(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, totalBeauty };
