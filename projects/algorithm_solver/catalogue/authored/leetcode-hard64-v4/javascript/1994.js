'use strict';

// 1994. The Number of Good Subsets. Square-free prime-mask DP and independent ones; O(n+30*2^10) time and O(2^10) space. Inputs are preserved.

function solve(nums) {
  const modulus = 1000000007;
  const frequency = Array(31).fill(0);
  for (const value of nums) frequency[value] += 1;
  const primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29];
  const ways = Array(1 << primes.length).fill(0);
  ways[0] = 1;
  for (let value = 2; value <= 30; value += 1) {
    if (frequency[value] === 0) continue;
    let mask = 0;
    let valid = true;
    for (let index = 0; index < primes.length; index += 1) {
      const prime = primes[index];
      if (value % (prime * prime) === 0) {
        valid = false;
        break;
      }
      if (value % prime === 0) mask |= 1 << index;
    }
    if (!valid) continue;
    for (let previous = ways.length - 1; previous >= 0; previous -= 1) {
      if ((previous & mask) === 0) {
        const following = previous | mask;
        ways[following] = (ways[following] + ways[previous] * frequency[value]) % modulus;
      }
    }
  }
  let answer = 0;
  for (let mask = 1; mask < ways.length; mask += 1) answer = (answer + ways[mask]) % modulus;
  for (let index = 0; index < frequency[1]; index += 1) answer = answer * 2 % modulus;
  return answer;
}

const numberOfGoodSubsets = solve;
class Solution {
  numberOfGoodSubsets(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfGoodSubsets };
