'use strict';

// 2572. Count the Number of Square-Free Subsets: combine disjoint prime masks while treating repeated nonunit values as exclusive choices.
// O(n + 30 * 2^10) time and O(2^10) auxiliary space; inputs are read-only.
function solve(nums) {
  const modulus = 1000000007;
  const primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29];
  const counts = new Int32Array(31);
  for (const value of nums) counts[value] += 1;
  let ways = new Array(1 << primes.length).fill(0);
  ways[0] = 1;
  for (let index = 0; index < counts[1]; index += 1) ways[0] = ways[0] * 2 % modulus;
  for (let value = 2; value <= 30; value += 1) {
    if (counts[value] === 0) continue;
    let mask = 0;
    let squareFree = true;
    for (let bit = 0; bit < primes.length; bit += 1) {
      const prime = primes[bit];
      if (value % (prime * prime) === 0) {
        squareFree = false;
        break;
      }
      if (value % prime === 0) mask |= 1 << bit;
    }
    if (!squareFree) continue;
    const updated = ways.slice();
    for (let used = 0; used < ways.length; used += 1) {
      if ((used & mask) === 0) {
        const target = used | mask;
        updated[target] = (updated[target] + ways[used] * counts[value]) % modulus;
      }
    }
    ways = updated;
  }
  let total = 0;
  for (const count of ways) total = (total + count) % modulus;
  return (total - 1 + modulus) % modulus;
}

const squareFreeSubsets = solve;
class Solution {
  squareFreeSubsets(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, squareFreeSubsets };
